import threading
import json
import requests
import time
import uuid
import asyncio
import traceback

from device_manager_service import Config
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from device_manager_service import generalLogger
from device_manager_service.models.events import (
    UserAddedDongleApiKeyEventType,
    UserUpdatedDongleApiKeyEventType,
    UserDongleSchema,
    UserHardDeletedEventType,
    UserAccountSchema
)

from marshmallow import ValidationError
from device_manager_service.models.db_models import db, DBProcessedEvent, DBDongles, DBShiftableMachine
# from sqlalchemy import OperationalError, DatabaseError
from sqlalchemy.exc import OperationalError, DatabaseError

from device_manager_service.utils.database.db_interactions import add_row_to_table, delete, add_and_commit

from temporalio.client import Client

import influxdb_client

from datetime import datetime, timezone


class AccountEventConsumers:
    def __init__(self):
        self.exitEvent = threading.Event()

        self.threads = {}

        # Create Kafka consumer threads
        thread = threading.Thread(name='consumer',
                                  target=consumer,
                                  args=(self.exitEvent,))

        self.threads['consumer'] = thread

    # Start threads
    def start(self):
        for thread in self.threads.values():
            thread.start()

    # Stop threads and wait for them to exit
    def stop(self):
        self.exitEvent.set()

        # Join all threads
        for thread in self.threads.values():
            # logging.info('Waiting for ' + thread + ' to exit')
            thread.join()


# Function that the thread is going to execute
def consumer(exitEvent):
    generalLogger.info("Configuring Kafka consumer...")

    # Loop to keep trying to connect to broker if it is not up or an exception occurs.
    while (exitEvent.is_set() == False):
        try:
            consumer = KafkaConsumer(
                Config.KAFKA_ACCOUNT_TOPIC,
                group_id=Config.KAFKA_GROUP_ID,
                bootstrap_servers=Config.KAFKA_BROKER_ENDPOINT,
                consumer_timeout_ms=Config.KAFKA_CONSUMER_TIMEOUT_MS,
                enable_auto_commit=False,
                auto_offset_reset='earliest',
                reconnect_backoff_ms=1000,
                reconnect_backoff_max_ms=5000,
                session_timeout_ms=20000,
                max_poll_records=50
            )
            # break

        except KafkaError as e:
            generalLogger.error(e)
            generalLogger.info(
                f'Reconnecting in {Config.KAFKA_RECONNECT_SLEEP_SECONDS} seconds...'
            )

            time.sleep(Config.KAFKA_RECONNECT_SLEEP_SECONDS)
            continue

        # if exitEvent.is_set():
        #     generalLogger.info('Consumer received event. Exiting...')
        #     return

        start = time.time()
        total_time = 0
        # Consume events until the program receives an exit signal
        while not exitEvent.wait(timeout=Config.KAFKA_WAIT_FOR_EVENT_SECONDS):

            current_time = time.time()
            if current_time - start >= 300:  # Log every x seconds
                total_time += 300
                generalLogger.info(
                    f"Kafka Event Consumer thread is healthy for {total_time} seconds....")
                start = current_time

            try:
                session = db.create_scoped_session()
                msg = next(consumer)
                processEvent(session, msg)
                consumer.commit()

            except StopIteration:
                pass

            except (OperationalError, DatabaseError) as e:
                generalLogger.error(repr(e))
                traceback.print_exc()
                session.rollback()
                session.close()
                consumer.commit()
                continue

            except Exception as e:
                generalLogger.error(
                    "Exception occured while listening for events")
                generalLogger.error(e)
                traceback.print_exc()
                session.close()
                break

            session.close()
            # Missing sending error event to other topic

    # Close connection to the broker
    consumer.close(autocommit=False)
    generalLogger.info('Consumer received event. Exiting...')


def processEvent(session, message):
    # Print the whole event
    # print(message)

    # Convert bytes to json and retrieve the "payload" field
    event = json.loads(message.value)
    eventId = event["payload"]["eventId"]
    eventType = payload = event["payload"]["eventType"]
    payload = event["payload"]["payload"]

    # Check if event has already been processed
    processedEvent = session.query(DBProcessedEvent).filter_by(
        event_type=eventType, event_id=eventId).first()
    if (processedEvent != None):
        generalLogger.error("Event " + eventType + "/" +
                            eventId + " already processed")
        return

    generalLogger.info(f"Processing event {eventId} / {eventType}")
    try:
        if eventType == UserAddedDongleApiKeyEventType or eventType == UserUpdatedDongleApiKeyEventType:
            processUserUpdatedDongleApiKeyEvent(
                session, eventId, eventType, payload)
        if eventType == UserHardDeletedEventType:
            processUserHardDeletedEvent(session, eventId, eventType, payload)
    except Exception as e:
        generalLogger.error(e)
        print(traceback.format_exc())


def processUserUpdatedDongleApiKeyEvent(session, eventId, eventType, payload):
    # Convert json to a python data structure
    dongleSchema = UserDongleSchema()
    try:
        payload = dongleSchema.loads(payload)
    except ValidationError as err:
        generalLogger.error(f"Failed to parse event payload: {err.messages}")
        return

    headers = {
        "X-Correlation-ID": str(uuid.uuid4())
    }

    # generalLogger.info(f"Getting list of dongles from account manager...")
    # dongles_response = requests.get(
    #     Config.ACCOUNT_MANAGER_ENDPOINT + "/list-dongles",
    #     headers=headers
    # )

    # dongles = dongles_response.json()
    # userIds = []

    # for dongle in dongles:
    #     if dongle["api_key"] == payload["api_key"]:
    #         userIds.append(dongle["user_id"])

    # if len(userIds) > 1:
    #     generalLogger.error(f'Dongle with ID {payload["api_key"]} already registered')
    #     return

    dongle = session.query(DBDongles).filter_by(
        user_id=payload["user_id"]).first()

    # If user is not yet registered on our DB, create a default row
    if (dongle == None):
        dongle = DBDongles(user_id=payload["user_id"])

        error_msg = f"Failed to add dongle {payload['api_key']} to DB"
        response_code = add_row_to_table(session, dongle, error_msg)
        if response_code != 200:
            return

    # If he has an API key already, then stop the old one from monitoring
    if (dongle.api_key != None):
        asyncio.run(removeDongleFromTemporal(session, dongle.api_key))
        dongle.api_key = None

    URL = "https://api.eot.pt/api/meter/feed.json?key=" + \
        payload["api_key"] + \
        "&results=1&channels[]=iap_diff&channels[]=ivl1&channels[]=ivl2&channels[]=ivl3"

    r = requests.get(URL)
    if (r.status_code != 200):
        generalLogger.error(
            f"URL check {URL} returned error status code {r.status_code}")
        processedEvent = DBProcessedEvent(
            event_type=eventType, event_id=eventId)

        error_msg = f"Failed to add processed event {eventType}/{eventId} to DB"
        response_code = add_and_commit(session, processedEvent, error_msg)

        return

    if (r.text == '-1'):
        generalLogger.error(f"URL check {URL} returned error: {r.text}")
        processedEvent = DBProcessedEvent(
            event_type=eventType, event_id=eventId)

        error_msg = f"Failed to add processed event {eventType}/{eventId} to DB"
        response_code = add_and_commit(session, processedEvent, error_msg)

        return

    asyncio.run(addDongleToTemporal(session, payload["api_key"]))

    dongle.api_key = payload["api_key"]

    # Save the event has processed
    processedEvent = DBProcessedEvent(event_type=eventType, event_id=eventId)

    error_msg = f"Failed to add processed event {eventType}/{eventId} to DB"
    response_code = add_and_commit(session, processedEvent, error_msg)

    generalLogger.info(f"Successfully processed event {eventId} / {eventType}")

    return


def processUserHardDeletedEvent(session, eventId, eventType, payload):
    generalLogger.info(f"Event Consumed: {eventType}\n")

    # Convert json to a python data structure
    userSchema = UserAccountSchema()
    try:
        payload = userSchema.loads(payload)
    except ValidationError as err:
        generalLogger.error(f"Failed to parse event payload: {err.messages}")
        return

    # client = await Client.connect(Config.TEMPORAL_URL)

    # workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + payload["user_id"] + "-" + payload["api_key"]

    # try:
    #     handle = client.get_workflow_handle(workflow_id=workflowID)
    #     result = await handle.cancel()
    #     generalLogger.info(f'Sucesfully stopped EOT Workflow for API key {payload["api_key"]}: {handle.id}, {handle.run_id}')
    # except Exception as e:
    #     generalLogger.error(f'Failed to stop EOT Workflow for API key {payload["api_key"]}')
    #     generalLogger.error(e)
    #     return

    dongle = session.query(DBDongles).filter_by(
        user_id=payload["user_id"]).first()

    # If user is not registered on our DB, then skip this "if"
    if (dongle != None):
        # If he has an API key, then stop it from monitoring
        if (dongle.api_key != None):
            asyncio.run(removeDongleFromTemporal(session, dongle.api_key))

        error_msg = f"Failed to delete dongle {dongle.api_key} from DB"
        response_code = delete(session, dongle, error_msg)
        if response_code != 200:
            return

    # Delete data from influx, meter_id and api_key
    client = influxdb_client.InfluxDBClient(
        url=f"http://{Config.INFLUX_URL}:{Config.INFLUX_PORT}",
        token=Config.INFLUX_TOKEN,
        org=Config.INFLUX_ORG
    )

    delete_api = client.delete_api()

    delete_api.delete(datetime.fromtimestamp(0).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), datetime(2200, 1, 1, tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"), f'_measurement="{dongle.api_key}"', bucket=Config.INFLUX_BUCKET, org=Config.INFLUX_ORG)

    delete_api.delete(datetime.fromtimestamp(0).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), datetime(2200, 1, 1, tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"), f'_measurement="{payload["meter_id"]}"', bucket=Config.INFLUX_BUCKET, org=Config.INFLUX_ORG)

    # Delete data from tables
    # settings = session.query(DBUserSettings).filter_by(user_id=payload['user_id']).first()
    # session.query(DBNotDisturb).filter_by(settings_id=settings.id).delete()
    session.query(DBShiftableMachine).filter_by(user_id=payload['user_id']).delete()
    session.query(DBDongles).filter_by(user_id=payload['user_id']).delete()

    # Save the event has processed
    processedEvent = DBProcessedEvent(event_type=eventType, event_id=eventId)

    error_msg = f"Failed to add processed event {eventType}/{eventId} to DB"
    response_code = add_and_commit(session, processedEvent, error_msg)
    if response_code != 200:
        return

    generalLogger.info(f"Successfully processed event {eventId} / {eventType}")

    return


async def addDongleToTemporal(session, deviceId):
    dongles = session.query(DBDongles).filter_by(api_key=deviceId).all()
    if (len(dongles) > 0):
        generalLogger.info(
            f"Not adding dongle with API key {deviceId} because another user also has it")
        return True

    client = await Client.connect(Config.TEMPORAL_URL)

    workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + deviceId

    try:
        handle = await client.start_workflow("EOTMonitorDevice", args=[deviceId], id=workflowID, task_queue=Config.TEMPORAL_DONGLE_TASK_QUEUE)
        generalLogger.info(
            f'Started to monitor dongle for API key {deviceId}: {handle.id}, {handle.run_id}')
    except Exception as e:
        generalLogger.error(f'Failed to monitor dongle for API key {deviceId}')
        generalLogger.error(e)
        return False

    return True


async def removeDongleFromTemporal(session, deviceId):
    dongles = session.query(DBDongles).filter_by(api_key=deviceId).all()
    if (len(dongles) > 1):
        generalLogger.info(
            f"Not removing dongle with API key {deviceId} because another user also has it")
        return True

    headers = {
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }
    generalLogger.info(f"Getting list of dongles from account manager...")
    dongles_response = requests.get(
        Config.ACCOUNT_MANAGER_ENDPOINT + "/list-dongles",
        headers=headers
    )

    dongles = dongles_response.json()
    userIds = []

    for dongle in dongles:
        if dongle["api_key"] == deviceId:
            userIds.append(dongle["user_id"])

    # If after the user removed his dongle id someone still has that api_key, return
    if len(userIds) > 0:
        generalLogger.error(
            f'Dongle with ID {deviceId} registered with more than one user')
        return True

    client = await Client.connect(Config.TEMPORAL_URL)

    workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + deviceId
    workflows = client.list_workflows(
        query=f'WorkflowId = "{workflowID}" and ExecutionStatus = "Running"')

    async for obj in workflows:
        try:
            handle = client.get_workflow_handle(workflow_id=obj.id)
            result = await handle.cancel()
            generalLogger.info(
                f'Sucesfully stopped EOT Workflow for API key {deviceId}: {handle.id}, {handle.run_id}')
        except Exception as e:
            generalLogger.error(
                f'Failed to stop EOT Workflow for API key {deviceId}')
            generalLogger.error(e)
            return False

    return True
