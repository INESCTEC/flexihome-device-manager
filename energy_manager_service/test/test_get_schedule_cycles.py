# coding: utf-8

from __future__ import absolute_import
import unittest, uuid, json
from datetime import datetime, timedelta

from energy_manager_service.test import BaseTestCase

from energy_manager_service.test import (
    clear_all_db,
    setup_test_env,
    schedule_cycle
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


class TestGetSchedules(BaseTestCase):
    
    
    def test_happy_flow(self):
        
        clear_all_db()
        serial_number = f"serialnumbertest"
        user_id, _, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=serial_number
        )
        
        
        get_schedule(self, user_id)
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)
        
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]['serial_number'], serial_number)
        self.assertEqual(json_response[0]['acceptance_request'], False)
    
    
    def test_two_cycles_happy_flow(self):
        
        clear_all_db()
        user_id, auth_token, device, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        start_date = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1, hours=8)).isoformat()
        schedule_cycle(auth_token, device['serial_number'], start_date)
        
        get_schedule(self, user_id)
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)
        
        self.assertEqual(len(json_response), 2)
        self.assertEqual(json_response[0]['serial_number'], device['serial_number'])
        self.assertEqual(json_response[1]['serial_number'], device['serial_number'])
        self.assertEqual(json_response[0]['acceptance_request'], False)
        self.assertEqual(json_response[1]['acceptance_request'], False)
    
    
    def test_cycle_without_recommendation_happy_flow(self):
        
        clear_all_db()
        user_id, auth_token, device, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        
        get_schedule(self, user_id)
        
        # Cycle scheduled after the scheduler optimization algorithm has run
        start_date = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1, hours=8)).isoformat()
        schedule_cycle(auth_token, device['serial_number'], start_date)
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)
        
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]['serial_number'], device['serial_number'])
        self.assertEqual(json_response[0]['sequence_id'], cycle['sequence_id'])
        self.assertEqual(json_response[0]['acceptance_request'], False)
    
    
    def test_no_cycles_happy_flow(self):
        
        clear_all_db()
        user_id, _, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        json_response = json.loads(response.data.decode('utf-8'))
        self.assert200(response, json_response)
        
        self.assertEqual(len(json_response), 0)
        
    
    def test_invalid_auth_token(self):
        
        clear_all_db()
        user_id, _, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': "invalid token"
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        self.assert401(response, response.data.decode('utf-8'))
        
        
    def test_user_trying_to_access_another_user(self):
            
        clear_all_db()
        _, auth_token, _, _ = setup_test_env()
        
        query_string = [('user_id', '1234567890')]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        self.assert403(response, response.data.decode('utf-8'))
        
        
    def test_non_existant_userid(self):
            
        clear_all_db()
        # user_id, _, _, _ = setup_test_env()
        
        query_string = [('user_id', '1234567890')]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        self.assert200(response, response.data.decode('utf-8'))
    
    
    def test_missing_userid_parameter(self):
        
        # clear_all_db()
        # _, _, _, _ = setup_test_env()
        
        query_string = []
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule/cycles',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        self.assert400(response, response.data.decode('utf-8'))
    
    
if __name__ == '__main__':
    unittest.main()
