import sys, uuid

sys.path.append("..")

from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility
from energy_manager_service.clients.hems_services.account_manager import get_user
from energy_manager_service.clients.hems_services.device_manager import list_devices
from energy_manager_service.test.setup_test_env import mock_forecast, user_login, schedule_cycle, set_automatic_management_of_device


unique_user_ids_with_available_flexibility = DBAvailableFlexbility.query.with_entities(
    DBAvailableFlexbility.user_id
).distinct()




for user_id in unique_user_ids_with_available_flexibility:
    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    
    try:
        # Get user info
        user_info, status_code = get_user(user_id['user_id'], cor_id)
        
        # login
        auth_token = user_login(user_info[0]['email'], password="654321", expo_token="v5h4HqOXDPRLLPCo0vkbTG")
        
        # get device info
        device_info, status_code = list_devices([user_id['user_id']])
        device_info = device_info[0]['devices'][0]
        
        # Schedule cycle
        schedule_cycle(auth_token, device_info['serial_number'])
        set_automatic_management_of_device(auth_token, device_info['serial_number'])
        
        # mock forecast
        mock_forecast(user_id['user_id'])
    
    except Exception as e:
        print(f"Error updating data for test user {user_id['user_id']}")
        print(repr(e))
        continue   
