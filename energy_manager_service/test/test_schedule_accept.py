# coding: utf-8

from __future__ import absolute_import
import unittest
import uuid
import json
from datetime import datetime, timedelta

from energy_manager_service.test import BaseTestCase

from energy_manager_service.test import (
    clear_all_db,
    setup_test_env,
    user_register_and_login,
    mock_energy_prices,
    mock_forecast,
    add_device,
    schedule_cycle,
    set_automatic_management_of_device,
    random_choice
)

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY


def get_schedule(flask_testing_client, user_id):
    query_string = [('user_id', user_id)]
    headers = {
        'Accept': 'application/json',
        'X-Correlation-ID': str(uuid.uuid4()),
    }
    response = flask_testing_client.client.open(
        '/api/energy_manager_service/schedule',
        method='GET',
        headers=headers,
        query_string=query_string
    )

    return response


class TestScheduleAccept(BaseTestCase):

    def test_happy_flow(self):

        clear_all_db()
        serial_number = f"serialnumbertest"
        user_id, auth_token, _, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=serial_number
        )

        get_schedule(self, user_id)

        query_string = {
            'user_id': user_id,
            'serial_number': serial_number,
            'sequence_id': cycle['sequence_id']
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)

    def test_internal_request_happy_flow(self):

        clear_all_db()
        serial_number = f"serialnumbertest"
        user_id, _, _, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=serial_number
        )

        get_schedule(self, user_id)

        query_string = {
            'user_id': user_id,
            'serial_number': serial_number,
            'sequence_id': cycle['sequence_id']
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)

        self.assertEqual(json_response, True)

    def test_no_recommendations_found_happy_flow(self):

        clear_all_db()
        serial_number = f"serialnumbertest"
        user_id, auth_token, _, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=serial_number
        )

        query_string = {
            'user_id': user_id,
            'serial_number': serial_number,
            'sequence_id': cycle['sequence_id']
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert404(response, json_response)

    def test_missing_query_parameters(self):

        clear_all_db()
        serial_number = f"serialnumbertest"
        user_id, auth_token, _, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=serial_number
        )

        # Missing sequence ID
        query_string = {
            'user_id': user_id,
            'serial_number': serial_number,
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert400(response, json_response)

        # Missing serial number
        query_string = {
            'user_id': user_id,
            'sequence_id': cycle['sequence_id']
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert400(response, json_response)

        # Missing user ID
        query_string = {
            'sequence_id': cycle['sequence_id'],
            'serial_number': serial_number,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/accept',
            method='POST',
            headers=headers,
            query_string=query_string
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assert400(response, json_response)


if __name__ == '__main__':
    unittest.main()
