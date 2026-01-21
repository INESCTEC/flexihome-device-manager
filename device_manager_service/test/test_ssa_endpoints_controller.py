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


class TestSSAEndpointsController(BaseTestCase):
    """SSAEndpointsController integration test stubs"""

    global user_key  # Key to create a new unique user in the db
    global user_id  # The randomly generated ID by the account manager
    global second_user_key
    global second_user_id

    def test_get_user_wp_appliances_get_service_availability(self):
        """Test case for get_user_wp_appliances_get

        Get appliances associated with the user's HotPoint Home Net account.
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

        # NOTE: Instead of the /get-user-wp-appliances endpoint, we will use the /list endpoint,
        # in order to reproduce representative HTTP response status codes for testing purposes.

        # ------------------------------ USER GETTING HIS OWN DEVICES ------------------------------ #

        query_string = {"user_ids": user_id}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        # response = self.client.open('/api/device/get-user-wp-appliances', method='GET', headers=headers, query_string=query_string)
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_get_user_wp_appliances_get_another_user(self):
        """Test case for get_user_wp_appliances_get

        Get appliances associated with the user's HotPoint Home Net account.
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

        # NOTE: Instead of the /get-user-wp-appliances endpoint, we will use the /list endpoint,
        # in order to reproduce representative HTTP response status codes for testing purposes.

        # ------------------------------ USER IS TRYING TO ACCESS AN ACCOUNT FROM ANOTHER USER (no permission) ------------------------------ #

        query_string = {"user_ids": second_user_id}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,  # auth for user 4c5e80dfjc, should not give permission to access other accounts
        }

        # response = self.client.open('/api/device/get-user-wp-appliances', method='GET', headers=headers, query_string=query_string)
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

    def test_get_user_wp_appliances_get_check_brand(self):
        """Test case for get_user_wp_appliances_get

        Get appliances associated with the user's HotPoint Home Net account.
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

        # NOTE: Instead of the /get-user-wp-appliances endpoint, we will use the /list endpoint,
        # in order to reproduce representative HTTP response status codes for testing purposes.

        # ------------------------------ USER GETTING HIS OWN DEVICES ------------------------------ #

        query_string = {"user_ids": user_id}
        headers = {
            "Accept": "application/json",
            "x_correlation_id": str(uuid.uuid4()),
            "Authorization": authorization,
        }

        # response = self.client.open('/api/device/get-user-wp-appliances', method='GET', headers=headers, query_string=query_string)
        response = self.client.open(
            "/api/device/device",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        response = json.loads(response.data.decode("utf-8"))
        response = response[
            0
        ]  # Because the defined schema does not include the array (only included in the path response)
        # validate(response, UserDeviceListSchema)

        count = 0
        for attribute in response["devices"]:
            print(attribute["brand"])
            if attribute["brand"] == "Whirlpool":
                count = count + 1
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
