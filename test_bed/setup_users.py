import sys, uuid, json, requests

sys.path.append("..")

# from device_manager_service import Config
from device_manager_service.test.helper_functions import (
    superuser_login,
    mock_register,
    clean_account
)


def mock_add_device(auth, serial_number, brand):
    device = {"serial_number": serial_number}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Correlation-ID": str(uuid.uuid4()),
        "Authorization": auth,
    }
    params = {"brand": brand}

    response = requests.post(
        "http://localhost:8080/api/device/device", 
        headers=headers, 
        params=params, 
        data=json.dumps(device)
    )
    print(response.status_code)
    print(response.content)

    return response


clean_account()

user_key, user_id, second_user_key, second_user_id = mock_register()

authorization = superuser_login(id=user_key)

print("addind device:")
_ = mock_add_device(
    authorization, serial_number="1113", brand="Whirlpool"
)