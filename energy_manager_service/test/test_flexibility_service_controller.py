# coding: utf-8

from __future__ import absolute_import
import unittest, uuid

from datetime import datetime, timezone, timedelta

from energy_manager_service import Config
from energy_manager_service.test import BaseTestCase
from energy_manager_service.test import (
    clear_all_db,
    setup_test_env
)

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY


# TODO: CLEAR ENERGY MANAGER DATABASE

class TestFlexibilityServiceController(BaseTestCase):
    """FlexibilityServiceController integration test stubs"""
    
    
    def calculate_asset_flexibility(self, asset_id):
        query_string = [('user_id', asset_id)]
        headers = { 
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4())
        }
        _ = self.client.open(
            '/api/energy_manager_service/flexibility/available',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        
        return

    def test_available_flexibility_get(self):
        """Test case for available_flexibility_get

        Build dayahead energy flexibility considering only appliances in the HEMS pool.
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
            'x_correlation_id': 'x_correlation_id_example'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/available',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    def test_flexibility_accept_post(self):
        """Test case for flexibility_accept_get

        Build dayahead energy schedule considering only appliances in the HEMS pool.
        """
        
        clear_all_db()
        user_id, _, _, _ = setup_test_env(
            email=f"vascampos25+test@gmail.com",
            meter_id=METER_ID,
            serial_number=f"serialnumbertest"
        )
        
        self.calculate_asset_flexibility(user_id)
        
        dt_now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        setpoints = []
        for i in range(0, 96):
            setpoints.append({
                "time_interval_start": dt_now.strftime(Config.TIMESTAMP_FORMAT),
                "time_interval_end": (dt_now + timedelta(minutes=15)).strftime(Config.TIMESTAMP_FORMAT),
                "power_value": 10
            })
        request_body = {
            "data_point": "dp",
            "creation_timestamp": dt_now.strftime(Config.TIMESTAMP_FORMAT),
            "setpoints": setpoints
        }
        
        query_string = [('asset', user_id)]
        headers = { 
            'Accept': 'application/json',
            'x_correlation_id': 'x_correlation_id_example'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=request_body
        )
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
