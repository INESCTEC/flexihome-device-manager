import sys, uuid, json, requests
from datetime import datetime, timedelta

sys.path.append("..")

# from device_manager_service import Config
from device_manager_service.test.helper_functions import (
    superuser_login
)

def mock_add_schedule(auth, serial_number):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Correlation-ID": str(uuid.uuid4()),
        "Authorization": auth,
    }
    params = {"serial_number": serial_number}
    body = {
        "program": "cotton",
        "scheduled_start_time": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    response = requests.post(
        "http://localhost:8084/api/device/schedule-cycle-by-device", 
        headers=headers, 
        params=params, 
        data=json.dumps(body)
    )
    print(response.status_code)
    print(response.content)

    return response


authorization = superuser_login(id="0", email="v.c+3@gmail.com", password="654321")

mock_add_schedule(authorization, serial_number="serial_number3")