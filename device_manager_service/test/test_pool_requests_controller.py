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
)


class TestPoolRequestsController(BaseTestCase):
    """PoolRequestsController integration test stubs"""

    global user_key  # Key to create a new unique user in the db
    global user_id  # The randomly generated ID by the account manager
    global second_user_key
    global second_user_id

    def test_perfect_pool_by_user_get_without_start_and_end_date(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = ""
        end_date = ""

        query_string = {
            "user_ids": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))

    def test_perfect_pool_by_user_get_with_start_date(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = datetime.now().date()
        end_date = ""

        query_string = {
            "user_ids": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))

    def test_perfect_pool_by_user_get_with_end_date(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = ""
        end_date = (datetime.now() + timedelta(hours=24)).date()

        query_string = {
            "user_ids": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))

    def test_perfect_pool_by_user_get_with_start_and_end_date(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = datetime.now().date()
        end_date = (datetime.now() + timedelta(hours=24)).date()

        query_string = {
            "user_ids": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_perfect_pool_by_user_get_another_user(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = datetime.now().date()
        end_date = (datetime.now() + timedelta(hours=24)).date()

        # ------------------------------ USER TRIES TO GET PERFECT POOL FROM OTHER USER' DEVICES (no permission) ------------------------------ #

        token = superuser_login(id=second_user_key)

        query_string = {
            "user_ids": user_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_perfect_pool_by_user_get_two_users(self):
        """Test case for perfect_pool_get
        Get perfect pools of user
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        start_date = datetime.now().date()
        end_date = (datetime.now() + timedelta(hours=24)).date()

        # ------------------------------ GET PERFECT POOLS FROM 2 USERS (no auth) ------------------------------ #

        query_string = {
            "user_ids": f"{user_id},{second_user_id}",
            "start_date": start_date,
            "end_date": end_date,
        }

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": token,
        }

        response = self.client.open(
            "/api/device/perfect-pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )

        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_pool_by_device_get(self):
        """Test case for pool_get
        Get schedule pool of devices
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        device = {"serial_number": device["serial_number"]}

        query_string = {"serial_numbers": "1116"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/pool-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_pool_by_device_get_another_user(self):
        """Test case for pool_get
        Get schedule pool of devices
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        device = {"serial_number": device["serial_number"]}

        query_string = {"serial_numbers": "1116"}

        # ------------------------------ USER TRIES TO GET POOL FROM OTHER USER' DEVICES (no permission) ------------------------------ #

        token = superuser_login(id=second_user_key)

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/pool-by-device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert404(response, "Response body is : " + response.data.decode("utf-8"))

    def test_pool_by_user_get(self):
        """Test case for pool_get
        Get schedule pool of devices
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        query_string = {"user_ids": user_id}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": uuid.uuid4(),
            "authorization": token,
        }

        response = self.client.open(
            "/api/device/pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_pool_by_user_get_two_users(self):
        """Test case for pool_get
        Get schedule pool of devices
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        # ------------------------------ GET POOLS FROM 2 USERS (no auth) ------------------------------ #

        query_string = {"user_ids": f"{user_id},{second_user_id}"}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": token,
        }

        response = self.client.open(
            "/api/device/pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_pool_by_user_get_another_user(self):
        """Test case for pool_get
        Get schedule pool of devices
        """
        clean_account()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        clean_database()

        token = superuser_login(id=user_key)

        device = mock_add_device(self, token, serial_number="1116", brand="Whirlpool")
        device = json.loads(device.data.decode("utf-8"))

        # ------------------------------ USER IS TRYING TO ACCESS THE POOLS FROM ANOTHER USER (no permission) ------------------------------ #

        token = superuser_login(id=second_user_key)

        query_string = {"user_ids": user_id}

        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "authorization": token,
        }
        response = self.client.open(
            "/api/device/pool-by-user",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
