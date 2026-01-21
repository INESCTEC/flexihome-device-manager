import sys

sys.path.append("..")

# from energy_manager_service import Config, generalLogger
from energy_manager_service.test.setup_test_env import setup_test_env


second_user = False
for i in range(10):
    i = str(i)
    
    user_id, auth_token, device_id, serial_number = setup_test_env(
        email=f"v.c+{i}@gmail.com",
        meter_id=f"meter{i}",
        serial_number=f"serial_number{i}",
        set_auto=False,
        second_user=second_user
    )
    
    second_user = True
