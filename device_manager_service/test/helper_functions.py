# coding: utf-8

from __future__ import absolute_import

from time import sleep
import uuid

from flask import json
import requests
from device_manager_service.config import Config
from device_manager_service import db

from device_manager_service.models.db_models import (
    DBConfirmationToken,
    DBUserSettings,
    DBNotDisturbUser,
    DBUser,
    DBEvent,
    DBShiftablePowerProfile,
    DBShiftableMachine,
    DBShiftableCycle,
    DBNotDisturb,
    DBDongles,
)
import asyncio
from temporalio.client import Client
import string
import secrets

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS



def clean_account():
    try:
        db.session.query(DBNotDisturbUser).delete()
        db.session.query(DBUserSettings).delete()
        db.session.query(DBEvent).delete()
        db.session.query(DBUser).delete()
        db.session.flush()
        db.session.commit()
    except:
        print("MOCK DATABASE - FAILED TO DELETE ACCOUNT DB")
        db.session.rollback()


def clean_database():
    try:
        db.session.query(DBNotDisturb).delete()
        db.session.query(DBShiftablePowerProfile).delete()
        db.session.query(DBShiftableCycle).delete()
        db.session.query(DBShiftableMachine).delete()
        db.session.query(DBDongles).delete()
        db.session.flush()
        db.session.commit()
    except:
        print("MOCK DATABASE - FAILED TO DELETE DB")
        db.session.rollback()


async def clean_temporal_workflows():
    client = await Client.connect(Config.TEMPORAL_URL)

    workflows = client.list_workflows(query='ExecutionStatus = "Running"')

    async for obj in workflows:
        try:
            handle = client.get_workflow_handle(workflow_id=obj.id)
            result = await handle.terminate()
            # print(f'Deleted workflow {obj.id}')
        except Exception as e:
            print(f'Failed to stop EOT Workflow with ID {obj.id}')
            print(e)
            exit(0)

async def count_running_workflows(workflow_id):
    client = await Client.connect(Config.TEMPORAL_URL)

    workflows = client.list_workflows(query=f'WorkflowId = "{workflow_id}" and ExecutionStatus = "Running"')

    result = 0

    async for obj in workflows:
        try:
            handle = client.get_workflow_handle(workflow_id=obj.id, run_id=obj.run_id)
            history = await handle.fetch_history()
            events = history.to_json_dict()["events"]
            status = False
            for event in events:
                if event["eventType"] == "EVENT_TYPE_WORKFLOW_EXECUTION_CANCEL_REQUESTED":
                    status = True
                    break
            
            if status == False:
                result = result + 1
            
            # result = await handle.terminate()
            # print(f'Deleted workflow {obj.id}')
        except Exception as e:
            print(f'Failed to stop EOT Workflow with ID {obj.id}')
            print(e)
            exit(0)
    
    # Debug logging
    # print(f"Checking {workflow_id}")
    # workflows = client.list_workflows(query=f'WorkflowId = "{workflow_id}"')
    # async for obj in workflows:
    #     # print(obj)
    #     try:
    #         handle = client.get_workflow_handle(workflow_id=obj.id, run_id=obj.run_id)
    #         history = await handle.fetch_history()
    #         events = history.to_json_dict()["events"]
    #         status = await handle.describe()
    #         print(obj.id)
    #         print(obj.run_id)
    #         print(status.status)
    #         print("\n")
    #     except Exception as e:
    #         print(f'Failed to stop EOT Workflow with ID {obj.id}')
    #         print(e)
    #         exit(0)
    
    return result


def id_generator(size, chars=string.ascii_lowercase + string.digits):
    return ''.join(secrets.SystemRandom().choice(chars) for _ in range(size))

METER_IDS_WITH_API_KEY = ["NLV_CLIENT_8585", "NLV_CLIENT_8813", "NLV_CLIENT_8819"]
METER_IDS_WITHOUT_API_KEY = ["NLV_CLIENT_9564", "NLV_CLIENT_9953"]

def register_super_user(id="aa", meter_id=METER_IDS_WITH_API_KEY[0]):
    body = {
            "first_name": "Test",
            "last_name": "Test",
            "email": f"riscas.cat1+{id}@gmail.com",
            "password": "123456",
            "password_repeat": "123456",
            "meter_id": meter_id,
            "country": "PT",
            "postal_code": "4450-001",
            "tarif_type": "simple",
            "contracted_power": "6.9 kVA",
            "schedule_type": "economic",
    }

    register_data = json.dumps(body)
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }

    print("REGISTERING USER....")
    new_user = requests.post(
        url=Config.ACCOUNT_MANAGER_ENDPOINT + "/register",
        data=register_data,
        headers=headers,
    )
    # new_user = requests.post(url="http://account-manager-test:8080/api/account"+ "/register", data=register_data, headers=headers)
    print(new_user.content)
    print("REGISTERING USER.... OK!")

    new_user_id = json.loads(new_user.content)["user_id"]
    print(new_user_id)

    print("Activate User Account")
    DBConfirmationToken.query.filter_by(user_id=new_user_id).delete()
    user = DBUser.query.filter_by(user_id=new_user_id).first()
    user.is_active = True
    # user.settings.permissions = "Full"

    db.session.commit()

    return new_user_id


def superuser_login(id="aa", email=None, password=None):
    if email is None:
        email = f"riscas.cat1+{id}@gmail.com"
    if password is None:
        password = "123456"
    login_data = json.dumps(
        {"email": email, "password": password}
    )
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }

    user_login = requests.post(
        url=Config.ACCOUNT_MANAGER_ENDPOINT + "/login", data=login_data, headers=headers
    )
    print(user_login.headers)

    return user_login.headers["authorization"]


def mock_add_device(test_client, auth, serial_number, brand):
    device = {"serial_number": serial_number}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x_correlation_id": str(uuid.uuid4()),
        "Authorization": auth,
    }
    params = {"brand": brand}
    response = test_client.client.open(
        "/api/device/device",
        method="POST",
        headers=headers,
        query_string=params,
        data=json.dumps(device),
        content_type="application/json",
    )

    return response



def mock_update_meter_id(auth, user_id, meter_id):
    headers = {
        "Accept": "application/json",
        "X-Correlation-ID": str(uuid.uuid4()),
        "Authorization": auth,
    }
    user = requests.get(
        url=f"{Config.ACCOUNT_MANAGER_ENDPOINT}/user?user-ids={user_id}",
        headers=headers,
    )

    user_dict = json.loads(user.content)[0]

    user_dict["meter_id"] = meter_id

    new_settings_data = json.dumps(user_dict)
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
        "Authorization": auth,
    }

    print("UPDATING USER....")
    user = requests.post(
        url=Config.ACCOUNT_MANAGER_ENDPOINT + "/user",
        data=new_settings_data,
        headers=headers,
    )
    # new_user = requests.post(url="http://account-manager-test:8080/api/account"+ "/register", data=register_data, headers=headers)
    print(user.content)

    if (user.status_code != 200):
        print("UPDATING USER.... ERROR!")
        return False
    
    print("UPDATING USER.... OK!")
    return True


def mock_delete_user(auth, user_id, delete_type="hard"):
    headers = {
        "Accept": "application/json",
        "X-Correlation-ID": str(uuid.uuid4()),
        "Authorization": auth,
    }
    user = requests.delete(
        url=f"{Config.ACCOUNT_MANAGER_ENDPOINT}/user?user-id={user_id}&delete_type={delete_type}",
        headers=headers,
    )

    if (user.status_code != 200):
        print("DELETING USER.... ERROR!")
        return False
    
    print("DELETING USER.... OK!")
    return True


def mock_add_schedule(test_client, auth, serial_number, start_time, program):

    cycle = {"scheduled_start_time": start_time, "program": program}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x_correlation_id": str(uuid.uuid4()),
        "Authorization": auth,
    }
    params = {"serial_numbers": serial_number}
    response = test_client.client.open(
        "/api/device/schedule-cycle-by-device",
        method="POST",
        headers=headers,
        query_string=params,
        data=json.dumps(cycle),
        content_type="application/json",
    )

    return response


def mock_register(user_key=None, meter_id=METER_IDS_WITH_API_KEY[0], meter_id_2=METER_IDS_WITH_API_KEY[1]):
    # clean_account()

    # Key to create a new unique user in the db
    # user_key = "aa"  # Must have 2 leters, because of the CPE naming convention
    if user_key == None:
        user_key = id_generator(3)

    user_id = register_super_user(
        id=user_key,
        meter_id=meter_id
    )  # The randomly generated ID by the account manager

    sleep(1)

    second_user_key = user_key + "b"
    second_user_id = register_super_user(id=second_user_key, meter_id=meter_id_2)

    sleep(1)

    return user_key, user_id, second_user_key, second_user_id


def mock_change_settings(test_client, auth, serial_number, not_disturb):

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x_correlation_id": str(uuid.uuid4()),
        "Authorization": auth,
    }
    params = {"serial_numbers": serial_number}
    response = test_client.client.open(
        "/api/device/settings-by-device",
        method="POST",
        headers=headers,
        query_string=params,
        data=json.dumps(not_disturb),
        content_type="application/json",
    )

    return response

def insert_data_influxdb(api_key, measurement):
    client = influxdb_client.InfluxDBClient(
        url=f"http://{Config.INFLUX_URL}:{Config.INFLUX_PORT}",
        token=Config.INFLUX_TOKEN,
        org=Config.INFLUX_ORG
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)

    data = []

    # Daily
    data.append(influxdb_client.Point(api_key).field(measurement, 19.1).time("2022-05-01T15:59:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 19.1).time("2022-05-01T23:59:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 20.3).time("2022-05-02T00:00:00+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 22.3).time("2022-05-02T00:01:00+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 25.3).time("2022-05-02T10:25:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 26.3).time("2022-05-02T23:50:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 28.9).time("2022-05-03T01:10:00+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 30.3).time("2022-05-03T23:25:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 33.3).time("2022-05-04T23:59:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 34.1).time("2022-05-05T03:00:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 38.3).time("2022-05-05T21:59:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 43.9).time("2022-05-06T05:45:30+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 45.5).time("2022-05-06T22:18:00+00:00"))
    data.append(influxdb_client.Point(api_key).field(measurement, 46.3).time("2022-05-07T01:00:30+00:00"))

    write_api.write(bucket=Config.INFLUX_BUCKET, org=Config.INFLUX_ORG, record=data)
