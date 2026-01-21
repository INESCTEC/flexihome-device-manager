# coding: utf-8

from __future__ import absolute_import
from datetime import datetime, timedelta

import unittest
import uuid

from flask import json
from device_manager_service.test import BaseTestCase

from device_manager_service.test.helper_functions import (
    clean_account,
    clean_database,
    superuser_login,
    mock_add_device,
    mock_register,
    mock_add_schedule,
)


class TestDeviceSchedulesController(BaseTestCase):
    """DeviceSchedulesController integration test stubs"""

    global user_key  # Key to create a new unique user in the db
    global user_id  # The randomly generated ID by the account manager
    global second_user_key
    global second_user_id

    def test_schedule_cycle_by_device_get_without_start_and_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF ONE DEVICE WITHOUT START_TIMESTAMP AND END_TIMESTAMP  ------------------------------ #

        blank_start_timestamp = ""
        blank_end_timestamp = ""

        query_string = {
            "serial_numbers": "1115",
            "start_timestamp": blank_start_timestamp,
            "end_timestamp": blank_end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_with_start_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF ONE DEVICE WITH START_TIMESTAMP ONLY  ------------------------------ #

        start_timestamp = datetime.now()
        blank_end_timestamp = ""

        query_string = {
            "serial_numbers": "1115",
            "start_timestamp": start_timestamp,
            "end_timestamp": blank_end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_with_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF ONE DEVICE WITH END_TIMESTAMP ONLY  ------------------------------ #

        blank_start_timestamp = ""
        end_timestamp = datetime.now() + +timedelta(hours=9)

        query_string = {
            "serial_numbers": "1115",
            "start_timestamp": blank_start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_with_start_and_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF MORE THAN ONE DEVICE WITH START_TIMESTAMP AND END_TIMESTAMP ------------------------------ #

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        query_string = {
            "serial_numbers": f'{"1113"},{"1115"}',
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_multiple_devices_another_user(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        # ------------------------------ USER TRIES TO GET SCHEDULES OF MULTIPLE DEVICES OF ANOTHER USER (no permission) ------------------------------ #

        authorization = superuser_login(id=second_user_key)

        query_string = {
            "serial_numbers": f'{"1113"},{"1115"}',
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_another_user(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        # ------------------------------ USER TRIES TO ACCESS SCHEDULE OF A SINGLE DEVICE OF ANOTHER USER (no permission) ------------------------------ #

        authorization = superuser_login(id=second_user_key)

        query_string = {
            "serial_numbers": "1115",
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_device_get_multiple_devices(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF MULTIPLE DEVICES  ------------------------------ #

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        query_string = {
            "serial_numbers": f'{"1113"},{"1115"}',
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_without_start_and_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF USERS WITHOUT START_TIMESTAMP AND END_TIMESTAMP ------------------------------ #

        blank_start_timestamp = ""
        blank_end_timestamp = ""

        query_string = {
            "user_ids": user_id,
            "start_timestamp": blank_start_timestamp,
            "end_timestamp": blank_end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_with_start_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES OF ONE DEVICE WITH START_TIMESTAMP ONLY ------------------------------ #

        start_timestamp = datetime.now()
        blank_end_timestamp = ""

        query_string = {
            "user_ids": user_id,
            "start_timestamp": start_timestamp,
            "end_timestamp": blank_end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_with_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES FROM 2 USERS WITH END_TIMESTAMP ONLY ------------------------------ #

        blank_start_timestamp = ""
        end_timestamp = datetime.now() + +timedelta(hours=9)

        query_string = {
            "user_ids": user_id,
            "start_timestamp": blank_start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_with_start_and_end_timestamp(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        # ------------------------------ GET SCHEDULES FROM 2 USERS WITH START_TIMESTAMP AND END_TIMESTAMP ------------------------------ #

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        query_string = {
            "user_ids": user_id,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))
        response = json.loads(response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_two_users(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        # ------------------------------ GET SCHEDULES FROM 2 USERS (no auth) ------------------------------ #

        query_string = {
            "user_ids": f"{user_id},{second_user_id}",
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_schedule_cycle_by_user_get_another_user(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=3),
            "cotton",
        )

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=6),
            "outdoor",
        )
        mock_add_schedule(
            self,
            authorization,
            device["serial_number"],
            datetime.now() + timedelta(hours=9),
            "easy_care",
        )

        start_timestamp = datetime.now()
        end_timestamp = datetime.now() + +timedelta(hours=9)

        # ------------------------------ USER IS TRYING TO ACCESS THE SCHEDULES FROM ANOTHER USER (no permission) ------------------------------ #

        query_string = {
            "user_ids": second_user_id,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/schedule-cycle-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
