# coding: utf-8

from __future__ import absolute_import
import unittest, uuid
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
    set_automatic_management_of_device
)

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY


class TestScheduler(BaseTestCase):

    def test_get_schedule_happy_flow(self):
        """Test happy flow, when the scheduler has every piece of data necessary to run its algorithm.
        """
        
        clear_all_db()
        user_id, auth_token, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response,'Response body is : ' + response.data.decode('utf-8'))
    
    
    def test_get_schedule_happy_flow_no_auth(self):
        """Test happy flow, when the scheduler has every piece of data necessary to run its algorithm
        with no authentication token (as being called from an internal service).
        """
        
        clear_all_db()
        user_id, _, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4())
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response,'Response body is : ' + response.data.decode('utf-8'))
        
    
    def test_get_schedule_two_different_users_happy_flow(self):
        """Test happy flow, when the scheduler has every piece of data necessary to run its algorithm.
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token, _, _ = setup_test_env(
            email=email,
            meter_id=meter_id,
            serial_number=f"serialnumbertest"
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response,'Response body is : ' + response.data.decode('utf-8'))
        
        
        user_id, auth_token, _, _ = setup_test_env(
            email=f"vascampos25+test1@gmail.com",
            meter_id=f"metertest1",
            serial_number=f"serialnumbertest1",
            second_user=True
        )
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response,'Response body is : ' + response.data.decode('utf-8'))
        
    
    def test_get_schedule_two_equal_schedules_without_auto_management(self):
        """Test happy flow, when the scheduler has every piece of data necessary to run its algorithm.
        """
        
        clear_all_db()
        user_id, auth_token, _, cycle = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response,'Response body is : ' + response.data.decode('utf-8'))
        
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn(f"the cycle {cycle['sequence_id'].lower()} is already optimized", response.data.decode('utf-8').lower())
        
    
    def test_get_schedule_two_equal_schedules_with_auto_management_rejected_by_device(self):
        """
        """
        
        clear_all_db()
        user_id, auth_token, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest",
            set_auto = True
        )
        
        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert403(response,'Response body is : ' + response.data.decode('utf-8'))
        self.assertIn("request was refused by the manufacturer", response.data.decode('utf-8').lower())


    def test_get_schedule_missing_user_id(self):
        """Test when the user id is missing.
        """
        
        clear_all_db()
        # _, auth_token, _, _ = setup_test_env()
        
        query_string = []
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert400(response,'Response body is : ' + response.data.decode('utf-8'))
        self.assertIn("Missing query parameter", response.data.decode('utf-8'))
    
    
    def test_get_schedule_invalid_auth_token(self):
        """Test with a real user id with an invalid auth token.
        """
        
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
            'Authorization': "aaaa",
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert400(response,'Response body is : ' + response.data.decode('utf-8'))
        # self.assertIn("Missing query parameter", response.data.decode('utf-8'))
    
    
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
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        self.assert403(response, response.data.decode('utf-8'))
    
    
    def test_get_schedule_userid_does_not_exist(self):
        """
        """
        
        clear_all_db()
        # mock_energy_prices()
        user_id = "aaaaaaaaaa"
        # mock_forecast(user_id)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4())
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response,'Response body is : ' + response.data.decode('utf-8'))
        
    
    def test_get_schedule_user_with_no_devices(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id,
        )
        
        mock_energy_prices()
        mock_forecast(user_id)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assertEqual(response.status_code, 202)
        self.assertIn("user has no cycles in pool", response.data.decode('utf-8').lower())
    
    
    def test_get_schedule_user_with_no_cycles(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id,
        )
        
        mock_energy_prices()
        mock_forecast(user_id)
        _ = add_device(auth_token, "Bosch", f"serialnumbertest")

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assertEqual(response.status_code, 202)
        self.assertIn("user has no cycles in pool", response.data.decode('utf-8').lower())
    
    
    def test_get_schedule_user_with_no_cycles_in_pool(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id
        )
        
        mock_energy_prices()
        mock_forecast(user_id)
        device = add_device(auth_token, "Bosch", f"serialnumbertest")
        set_automatic_management_of_device(auth_token, device['serial_number'])
        
        start_time = (datetime.now() + timedelta(days=2)).isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)
        start_time = (datetime.now() - timedelta(hours=5)).isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)
        start_time = datetime.now().isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assertEqual(response.status_code, 202)
        self.assertIn("user has no cycles in pool", response.data.decode('utf-8').lower())
        

    def test_get_schedule_user_cycle_delay_fails(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id
        )
        
        mock_energy_prices()
        mock_forecast(user_id)
        device = add_device(auth_token, "Bosch", f"serialnumbertest")
        
        start_time = (datetime.now().replace(hour=12) + timedelta(days=1)).isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert403(response,'Response body is : ' + response.data.decode('utf-8'))
        # self.assertIn("user has no cycles in pool", response.data.decode('utf-8').lower())
        
    
    # NOTE: Energy Prices (ERSE TARIFFS) can only fail if service is unavailable for some reason
    
    # def test_get_schedule_no_energy_prices(self):
    #     """
    #     """
        
    #     clear_all_db()
    #     # clear_energy_prices_db(conn_prices)
    #     email = f"vascampos25+test@gmail.com"
    #     meter_id = METER_ID
    #     user_id, auth_token = user_register_and_login(
    #         email, meter_id
    #     )
        
    #     mock_forecast(user_id)

        
    #     query_string = [('user_id', user_id)]
    #     headers = { 
    #         'Accept': 'application/json',
    #         'X-Correlation-ID': str(uuid.uuid4()),
    #         'Authorization': auth_token,
    #     }
    #     response = self.client.open(
    #         '/api/energy_manager_service/schedule',
    #         method='GET',
    #         headers=headers,
    #         query_string=query_string
    #     )
    #     self.assert404(response,'Response body is : ' + response.data.decode('utf-8'))
        
        # set energy prices again
        # mock_energy_prices()
        # mock_energy_prices(days_delta=1)
    
    
    # def test_get_schedule_energy_prices_wrong_format(self):
    #     """
    #     """
        
    #     clear_all_db()
    #     clear_energy_prices_db(conn_prices)
        
    #     email = f"vascampos25+test@gmail.com"
    #     meter_id = METER_ID
    #     user_id, auth_token = user_register_and_login(
    #         email, meter_id
    #     )
        
    #     mock_energy_prices(step=95)
    #     mock_forecast(user_id)
    #     device = add_device(auth_token, "Bosch", f"serialnumbertest")
    #     start_time = (datetime.now().replace(hour=12) + timedelta(days=1)).isoformat()
    #     _ = schedule_cycle(auth_token, device['serial_number'], start_time)

        
    #     query_string = [('user_id', user_id)]
    #     headers = { 
    #         'Accept': 'application/json',
    #         'X-Correlation-ID': str(uuid.uuid4()),
    #         'Authorization': auth_token,
    #     }
    #     response = self.client.open(
    #         '/api/energy_manager_service/schedule',
    #         method='GET',
    #         headers=headers,
    #         query_string=query_string
    #     )
    #     self.assert400(response,'Response body is : ' + response.data.decode('utf-8'))
        
    #     # set energy prices again
    #     mock_energy_prices()
    #     mock_energy_prices(days_delta=1)
        
        
    def test_get_schedule_no_forecast(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id
        )
        
        mock_energy_prices()
        device = add_device(auth_token, "Bosch", f"serialnumbertest")
        start_time = (datetime.now().replace(hour=12) + timedelta(days=1)).isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response,'Response body is : ' + response.data.decode('utf-8'))


    def test_get_schedule_forecast_wrong_format(self):
        """
        """
        
        clear_all_db()
        email = f"vascampos25+test@gmail.com"
        meter_id = METER_ID
        user_id, auth_token = user_register_and_login(
            email, meter_id
        )
        
        mock_energy_prices()
        mock_forecast(user_id, step=23)
        device = add_device(auth_token, "Bosch", f"serialnumbertest")
        start_time = (datetime.now().replace(hour=12) + timedelta(days=1)).isoformat()
        _ = schedule_cycle(auth_token, device['serial_number'], start_time)

        
        query_string = [('user_id', user_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            'Authorization': auth_token,
        }
        response = self.client.open(
            '/api/energy_manager_service/schedule',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert400(response,'Response body is : ' + response.data.decode('utf-8'))
    

if str(uuid.uuid4()) == '__main__':
    unittest.main()
