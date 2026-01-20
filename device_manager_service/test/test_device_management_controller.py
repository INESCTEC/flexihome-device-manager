# coding: utf-8

from __future__ import absolute_import

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
    mock_change_settings,
)

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

    def test_list_get_user_own_devices(self):
        """Test case for list_get

        List devices from user accounts.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Whirlpool"
        )
        _ = mock_add_device(
            self, authorization, serial_number="1114", brand="Whirlpool"
        )
        _ = mock_add_device(self, authorization, serial_number="1112", brand="BSH")

        # ------------------------------ USER GETTING HIS OWN DEVICES ------------------------------ #

        query_string = {"user_ids": user_id}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        response = json.loads(response.data.decode("utf-8"))
        response = response[
            0
        ]  # Because the defined schema does not include the array (only included in the path response)
        # validate(response, UserDeviceListSchema)
        self.assertEqual(len(response["devices"]), 3)

    def test_list_get_two_users(self):
        """Test case for list_get

        List devices from user accounts.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Whirlpool"
        )
        _ = mock_add_device(
            self, authorization, serial_number="1114", brand="Whirlpool"
        )
        _ = mock_add_device(self, authorization, serial_number="1112", brand="BSH")

        # ------------------------------ GET LIST OF DEVICES FROM 2 USERS (no auth) ------------------------------ #

        query_string = {"user_ids": f"{user_id},{second_user_id}"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_get_user_accesses_multiple_user_accounts(self):
        """Test case for list_get

        List devices from user accounts.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Whirlpool"
        )
        _ = mock_add_device(
            self, authorization, serial_number="1114", brand="Whirlpool"
        )
        _ = mock_add_device(self, authorization, serial_number="1112", brand="BSH")

        # ------------------------------ USER IS TRYING TO ACCESS MULTIPLE USER ACCOUNTS (no permission) ------------------------------ #

        query_string = {"user_ids": f"{user_id},{second_user_id}"}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,  # auth for user 4c5e80dfjc, should not give permission to access other accounts
        }
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_get_user_accesses_another_user_account(self):
        """Test case for list_get

        List devices from user accounts.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Whirlpool"
        )
        _ = mock_add_device(
            self, authorization, serial_number="1114", brand="Whirlpool"
        )
        _ = mock_add_device(self, authorization, serial_number="1112", brand="BSH")

        # ------------------------------ USER IS TRYING TO ACCESS AN ACCOUNT FROM ANOTHER USER (no permission) ------------------------------ #

        query_string = {"user_ids": second_user_id}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,  # auth for user 4c5e80dfjc, should not give permission to access other accounts
        }
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_remove_device_post(self):
        """Test case for remove_device_post

        Remove device from user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1117", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        device = {"serial_number": device["serial_number"]}

        query_string = {"serial_number": "1117", "delete_type": "hard"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }
        response = self.client.open(
            "/api/device/device",
            method="DELETE",
            headers=headers,
            query_string=query_string,
            data=json.dumps(device),
            content_type="application/json",
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_settings_by_device_get_single_device(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        not_disturb = NOT_DISTURB

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))

        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        # ------------------------------ GET SETTINGS OF ONE DEVICE ------------------------------ #

        query_string = {"serial_numbers": "1115"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            "/api/device/settings-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_settings_by_device_get_multiple_devices(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        not_disturb = NOT_DISTURB

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))

        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        # ------------------------------ GET SETTINGS OF MULTIPLE DEVICES ------------------------------ #

        query_string = {"serial_numbers": f'{"1113"},{"1115"}'}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        response = self.client.open(
            "/api/device/settings-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_settings_by_device_get_single_device_of_another_user(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        not_disturb = NOT_DISTURB

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))

        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        # ------------------------------ USER TRIES TO GET SETTINGS OF A SINGLE DEVICE FROM ANOTHER USER (no permission) ------------------------------ #

        authorization = superuser_login(id=second_user_key)

        query_string = {"serial_numbers": "1113"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/settings-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_settings_by_device_get_multiple_devices_of_another_user(self):
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        authorization = superuser_login(id=user_key)

        not_disturb = NOT_DISTURB

        device = mock_add_device(
            self, authorization, serial_number="1115", brand="Whirlpool"
        )
        device = json.loads(device.data.decode("utf-8"))
        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        device = mock_add_device(self, authorization, serial_number="1113", brand="BSH")
        device = json.loads(device.data.decode("utf-8"))

        mock_change_settings(self, authorization, device["serial_number"], not_disturb)

        # ------------------------------ USER TRIES TO GET SETTINGS OF MULTIPLE DEVICES OF ANOTHER USER (no permission) ------------------------------ #

        authorization = superuser_login(id=second_user_key)

        query_string = {"serial_numbers": f'{"1113"},{"1115"}'}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": authorization,
        }
        response = self.client.open(
            "/api/device/settings-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()