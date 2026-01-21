import json
from kafka.errors import KafkaError
from kafka import KafkaProducer
import uuid
from datetime import datetime, timedelta, timezone
import time
import requests
import sys
sys.path.append('../../..')
from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility
from energy_manager_service import generalLogger, Config

FlexibilityNotAcceptedByGridNotificationType = "FlexibilityNotAcceptedByGridNotification"


def send_notifications_flexibility_not_accepted_by_grid():
    generalLogger.info(
        f'Starting to send notifications to users that did not have their available flexibilites accepted by the grid for tomorrow...')

    generalLogger.debug(
        f"Connecting to Kafka broker at {Config.KAFKA_BOOTSTRAP_SERVERS}...")
    connection_attempts = Config.KAFKA_CONNECTION_ATTEMPTS
    kafka_producer = None
    while connection_attempts > 0:
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[Config.KAFKA_BOOTSTRAP_SERVERS], retries=5)
            break
        except KafkaError as e:
            generalLogger.error(e)
            generalLogger.info(
                f'Reconnecting in {Config.KAFKA_RECONNECT_SLEEP_SECONDS} seconds...'
            )

            kafka_producer = None
            time.sleep(Config.KAFKA_RECONNECT_SLEEP_SECONDS)

    if kafka_producer is None:
        generalLogger.error(f"Failed to connect to Kafka broker. Exiting...")

    generalLogger.info(
        f'Retrieving all available flexibilities of all meter IDs that were not accepted by the grid for tomorrow...')

    request_timestamp_start = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    request_timestamp_end = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0)
    request_timestamp_start = request_timestamp_start.astimezone(
        tz=timezone.utc)
    request_timestamp_end = request_timestamp_end.astimezone(tz=timezone.utc)

    flexs = DBAvailableFlexbility.query.distinct(
        DBAvailableFlexbility.meter_id
    ).filter_by(
        baseline_zeros=False,
        flex_up_zeros=False
    ).filter(
        DBAvailableFlexbility.request_datetime >= request_timestamp_start,
        DBAvailableFlexbility.request_datetime < request_timestamp_end
    ).order_by(
        DBAvailableFlexbility.meter_id, DBAvailableFlexbility.request_datetime.desc()
    ).all()

    generalLogger.info(
        "Successfully got all available flexibilities of all meter IDs that were not accepted by the grid for tomorrow.")

    if len(flexs) == 0:
        generalLogger.warning(
            "No available flexibilities to process. Exiting...")
        return

    generalLogger.info(f"Number of flexibilities returned: {len(flexs)}")

    for flex in flexs:
        if flex.accepted_by_grid is True:
            continue

        generalLogger.info(
            f'The latest available flexibility for the user with ID {flex.user_id} was not accepted by the grid. Sending notification...')

        payload = {"user_id": flex.user_id, "language": "PT"}
        event = {"eventId": str(uuid.uuid4()),
                 "eventType": FlexibilityNotAcceptedByGridNotificationType,
                 "payload": payload
                 }

        kafka_producer.send(Config.KAFKA_TOPIC_NOTIFICATION,
                            json.dumps(event).encode())

    kafka_producer.flush()

    generalLogger.info(
        'Send notifications to users that did not have their available flexibilites accepted by the grid for tomorrow completed. Exiting...')


if __name__ == "__main__":
    send_notifications_flexibility_not_accepted_by_grid()
