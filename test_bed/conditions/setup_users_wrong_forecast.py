import sys, uuid

sys.path.append("../..")

from energy_manager_service.clients.hems_services.device_manager import list_devices
from energy_manager_service.test.setup_test_env import mock_forecast, add_device, schedule_cycle, set_automatic_management_of_device, user_register_and_login




for i in range(5):
    email = "test_user+" + str(i) + "@gmail.com"
    meter_id = "meter" + str(i)
    serial_number = "serial_number" + str(i)

    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    
    try:
        # register and login
        user_id, auth_token = user_register_and_login(email, meter_id)
        
        # Add device
        device = add_device(auth_token, brand="Bosch", serial_number=serial_number)
        
        # Schedule cycle
        schedule_cycle(auth_token, serial_number)
        set_automatic_management_of_device(auth_token, serial_number)
        
        # mock forecast
        mock_forecast(user_id, step=22)
    
    except Exception as e:
        print(f"Error creating data for test user {email}")
        print(repr(e))
        continue   