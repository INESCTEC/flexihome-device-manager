# coding: utf-8

from __future__ import absolute_import

import unittest
import uuid

from flask import json
from device_manager_service.test import BaseTestCase
from device_manager_service.test.helper_functions import (
    clean_account,
    clean_database,
    clean_temporal_workflows,
    superuser_login,
    mock_add_device,
    mock_register,
    mock_change_settings,
    mock_update_meter_id,
    count_running_workflows,
    mock_delete_user,
    METER_IDS_WITH_API_KEY,
    METER_IDS_WITHOUT_API_KEY,
    insert_data_influxdb
)
from device_manager_service.models.db_models import DBDongles, DBShiftableMachine, DBShiftableCycle, DBShiftablePowerProfile
from time import sleep
import asyncio
from temporalio.client import Client
from device_manager_service.config import Config

from datetime import datetime, timedelta, timezone
import requests
import influxdb_client


NOT_DISTURB = {
    "sunday": [
        {
            "start_timestamp": "05-06-2022T00:00:00Z",
            "end_timestamp": "05-06-2022T10:00:00Z",
        },
        {
            "start_timestamp": "05-06-2022T20:00:00Z",
            "end_timestamp": "05-06-2022T23:59:59Z",
        },
    ],
    "monday": [
        {
            "start_timestamp": "06-06-2022T00:00:00Z",
            "end_timestamp": "06-06-2022T09:00:00Z",
        }
    ],
    "tuesday": [
        {
            "start_timestamp": "07-06-2022T20:00:00Z",
            "end_timestamp": "07-06-2022T21:00:00Z",
        }
    ],
    "wednesday": [
        {
            "start_timestamp": "08-06-2022T10:00:00Z",
            "end_timestamp": "08-06-2022T11:00:00Z",
        }
    ],
    "thursday": [
        {
            "start_timestamp": "09-06-2022T22:00:00Z",
            "end_timestamp": "09-06-2022T23:00:00Z",
        }
    ],
    "friday": [
        {
            "start_timestamp": "10-06-2022T21:00:00Z",
            "end_timestamp": "10-06-2022T23:00:00Z",
        }
    ],
    "saturday": [
        {
            "start_timestamp": "11-06-2022T20:00:00Z",
            "end_timestamp": "11-06-2022T23:00:00Z",
        }
    ],
}


class TestDeviceManagementController(BaseTestCase):
    """DeviceManagementController integration test stubs"""

    global user_key  # Key to create a new unique user in the db
    global user_id  # The randomly generated ID by the account manager
    global second_user_key
    global second_user_id
    
    def test_user_register_meter_id(self):
        """Test case for event when user registers their meter id
        """
        clean_account()
        clean_database()
        asyncio.run(clean_temporal_workflows())

        meter_id = "NLV_CLIENT_8585"
        api_key = "XXX"

        user_key, user_id, second_user_key, second_user_id = mock_register(None, meter_id)

        authorization = superuser_login(id=user_key)

        dongle = None
        tries = 3
        while (dongle is None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id).first()
            if dongle is None:
                tries = tries - 1
        
        self.assertIsNotNone(dongle)
        self.assertEqual(dongle.user_id, user_id)
        self.assertEqual(dongle.api_key, api_key)

        client = asyncio.run(Client.connect(Config.TEMPORAL_URL))
        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 1)
    
    def test_user_delete_meter_id(self):
        """Test case for event when user is deleted
        """
        clean_account()
        clean_database()
        asyncio.run(clean_temporal_workflows())

        meter_id = "NLV_CLIENT_8585"
        api_key = "XXX"

        user_key, user_id, second_user_key, second_user_id = mock_register(None, meter_id)

        authorization = superuser_login(id=user_key)

        dongle = None
        tries = 3
        while (dongle is None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id).first()
            if dongle is None:
                tries = tries - 1
        
        self.assertIsNotNone(dongle)
        self.assertEqual(dongle.user_id, user_id)
        self.assertEqual(dongle.api_key, api_key)

        client = asyncio.run(Client.connect(Config.TEMPORAL_URL))
        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 1)

        # Delete user
        success = mock_delete_user(authorization, user_id)
        self.assertTrue(success)

        dongle = DBDongles.query.filter_by(user_id=user_id).first()
        tries = 3
        while (dongle is not None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id).first()
            if dongle is not None:
                tries = tries - 1
        
        self.assertIsNone(dongle)

        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 0)


    def test_user_updated_meter_id(self):
        """Test case for event when user updates their meter_id
        """
        clean_account()
        clean_database()
        asyncio.run(clean_temporal_workflows())

        meter_id = "NLV_CLIENT_8585"
        api_key = "XXX"

        meter_id_2 = "NLV_CLIENT_8813"
        api_key_2 = "XXX"

        meter_id_3 = "NLV_CLIENT_8819"
        api_key_3 = "XXX"

        user_key, user_id, second_user_key, second_user_id = mock_register(None, meter_id=meter_id, meter_id_2=meter_id_2)

        authorization = superuser_login(id=user_key)

        dongle = None
        tries = 3
        while (dongle is None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id).first()
            if dongle is None:
                tries = tries - 1
        
        self.assertIsNotNone(dongle)
        self.assertEqual(dongle.user_id, user_id)
        self.assertEqual(dongle.api_key, api_key)
        
        client = asyncio.run(Client.connect(Config.TEMPORAL_URL))
        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 1)


        success = mock_update_meter_id(authorization, user_id, meter_id_3)
        self.assertTrue(success)

        dongle = DBDongles.query.filter_by(user_id=user_id, api_key=api_key).first()
        tries = 3
        while (dongle is not None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id, api_key=api_key).first()
            if dongle is not None:
                tries = tries - 1

        self.assertIsNone(dongle)

        dongle = None
        tries = 3
        while (dongle is None) & (tries > 0):
            sleep(2)
            dongle = DBDongles.query.filter_by(user_id=user_id).first()
            if dongle is None:
                tries = tries - 1

        self.assertIsNotNone(dongle)
        self.assertEqual(dongle.user_id, user_id)
        self.assertEqual(dongle.api_key, api_key_3)

        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 0)

        # client = asyncio.run(Client.connect(Config.TEMPORAL_URL))
        sleep(1)
        workflowID = Config.TEMPORAL_WORKFLOW_ID_PREFIX + api_key_3
        count = asyncio.run(count_running_workflows(workflowID))

        self.assertEqual(count, 1)
    
    def test_user_register_meter_id(self):
        """Test case for event when user registers their meter id
        """
        clean_account()
        clean_database()
        asyncio.run(clean_temporal_workflows())

        meter_id = "NLV_CLIENT_8585"
        api_key = "XXX"
        influx_variable = "energyImported"

        user_key, user_id, second_user_key, second_user_id = mock_register(None, meter_id)

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Bosch"
        )

        headers = {
        "X-Correlation-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Authorization": authorization
        }
        
        query_params = {
            "serial_number": "1113"
        }

        response = self.client.open(
            "/api/device/device/settings/set-automatic-management",
            method="POST",
            headers=headers,
            query_string=query_params,
        )

        start_time = (datetime.now().replace(hour=0) + timedelta(days=1, hours=12)).isoformat()
        schedule_cycle_body = {
            "scheduled_start_time": start_time,
            "program": "cotton"
        }
        
        response = self.client.open(
            '/api/device/schedule-cycle-by-device',
            method="POST",
            headers=headers,
            query_string=query_params,
            data=json.dumps(schedule_cycle_body),
            content_type="application/json",
        )

        cycle = json.loads(response.data.decode("utf-8"))
    
        print(f"Cycle scheduled... {response.status_code}")

        insert_data_influxdb(api_key, influx_variable)

        query_string = {"user-id": user_id, "delete_type": "hard"}

        response = requests.delete(
            f'{Config.ACCOUNT_MANAGER_ENDPOINT}/user',
            headers=headers,
            params=query_string,
        )

        self.assert200(response, "Response body is : " + response.content.decode("utf-8"))

        sleep(10)
        
        shiftMachine = DBShiftableMachine.query.filter_by().first()
        shiftCycle = DBShiftableCycle.query.filter_by().first()
        shiftPowerProfile = DBShiftablePowerProfile.query.filter_by().first()
        dongle = DBDongles.query.filter_by(user_id=user_id).first()

        self.assertIsNone(shiftMachine)
        self.assertIsNone(shiftCycle)
        self.assertIsNone(shiftPowerProfile)
        self.assertIsNone(dongle)

        client = influxdb_client.InfluxDBClient(
            url=f"http://{Config.INFLUX_URL}:{Config.INFLUX_PORT}",
            token=Config.INFLUX_TOKEN,
            org=Config.INFLUX_ORG
        )

        query_api = client.query_api()

        query = f"""from(bucket: "{Config.INFLUX_BUCKET}")
                |> range(start: 0, stop: {int(datetime.now(timezone.utc).timestamp())})
                |> filter(fn: (r) => r["_measurement"] == "{api_key}")
                |> filter(fn: (r) => r["_field"] == "{influx_variable}")
                |> yield(name: "{influx_variable}")"""
        
        result = query_api.query(query=query)

        self.assertEqual(len(result), 0)

if __name__ == "__main__":
    unittest.main()