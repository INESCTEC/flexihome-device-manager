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
)


class TestMockEndpointsController(BaseTestCase):
    """MockEndpointsController integration test stubs"""

    global user_key  # Key to create a new unique user in the db
    global user_id  # The randomly generated ID by the account manager
    global second_user_key
    global second_user_id

    def test_add_device(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))
        # response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

    def test_add_device_check_id(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # self.assert200(response, "Response body is : " + response.data.decode("utf-8"))
        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["serial_number"], "1111")

    def test_add_device_check_brand(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["brand"], "BSH")

    def test_add_device_check_serial_number(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["serial_number"], "1111")

    def test_add_device_different_brand(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # ------------------------------ DIFFERENT BRAND ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_add_device_different_brand_check_id(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # ------------------------------ DIFFERENT BRAND ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["serial_number"], "1111")

    def test_add_device_different_brand_check_brand(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # ------------------------------ DIFFERENT BRAND ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["brand"], "Whirlpool")

    def test_add_device_different_brand_check_serial_number(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # ------------------------------ DIFFERENT BRAND ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        response = json.loads(response.data.decode("utf-8"))
        # validate(response, DeviceSchema)

        self.assertEqual(response["serial_number"], "1111")

    def test_add_device_different_brand_check_existing_device(self):
        """Test case for test_add_device

        Add device to user account.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        # ------------------------------ NORMAL ADD REQUEST ------------------------------ #

        authorization = superuser_login(id=user_key)

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="BSH"
        )

        # ------------------------------ DIFFERENT BRAND ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        # ------------------------------ DEVICE ID ALREADY EXISTS ------------------------------ #

        response = mock_add_device(
            self, authorization, serial_number="1111", brand="Whirlpool"
        )

        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))
        print(f"\n{json.loads(response.data.decode('utf-8'))}\n")

    def test_get_list_devices(self):
        """Test case for list_get

        List devices from user accounts.
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()
        # user_key, user_id, _, second_user_id = mock_register()

        # ------------------------------ USER GETTING HIS OWN DEVICES ------------------------------ #

        authorization = superuser_login(id=user_key)

        _ = mock_add_device(
            self, authorization, serial_number="1113", brand="Whirlpool"
        )
        _ = mock_add_device(
            self, authorization, serial_number="1114", brand="Whirlpool"
        )
        _ = mock_add_device(self, authorization, serial_number="1112", brand="BSH")

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


if __name__ == "__main__":
    unittest.main()
