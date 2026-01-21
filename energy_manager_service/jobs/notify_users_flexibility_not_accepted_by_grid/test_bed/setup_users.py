from helper_functions import create_available_flex
from helper_functions import (
    superuser_login,
    mock_register,
    get_user,
    clean_account,
    clean_database,
    METER_IDS_WITH_API_KEY
)
# import sys
import uuid
import json
import requests

from datetime import datetime, timedelta, timezone

import sys
sys.path.append("../../../")


# def mock_add_device(auth, serial_number, brand):
#     device = {"serial_number": serial_number}
#     headers = {
#         "Accept": "application/json",
#         "Content-Type": "application/json",
#         "X-Correlation-ID": str(uuid.uuid4()),
#         "Authorization": auth,
#     }
#     params = {"brand": brand}

#     response = requests.post(
#         "http://localhost:8082/api/device/device",
#         headers=headers,
#         params=params,
#         data=json.dumps(device)
#     )
#     print(response.status_code)
#     print(response.content)

#     return response


# def mock_add_schedule(auth, serial_number):
#     headers = {
#         "Accept": "application/json",
#         "Content-Type": "application/json",
#         "X-Correlation-ID": str(uuid.uuid4()),
#         "Authorization": auth,
#     }
#     params = {"serial_number": serial_number}
#     body = {
#         "program": "cotton",
#         "scheduled_start_time": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
#     }

#     response = requests.post(
#         "http://localhost:8082/api/device/schedule-cycle-by-device",
#         headers=headers,
#         params=params,
#         data=json.dumps(body)
#     )
#     print(response.status_code)
#     print(response.content)

#     return response


clean_account()
clean_database()

user_key, user_id, second_user_key, second_user_id, third_user_key, third_user_id = mock_register()

authorization = superuser_login(
    id=user_key, expo_token="z8GZ8sAKOhqUU5CNb-x1gN")
second_authorization = superuser_login(id=second_user_key)

# print("addind device:")
# _ = mock_add_device(
#     authorization, serial_number="AAAA", brand="Whirlpool"
# )

# mock_add_schedule(authorization, serial_number="AAAA")

# print("addind device:")
# _ = mock_add_device(
#     second_authorization, serial_number="BBBB", brand="Whirlpool"
# )

# First user: two flexibilities. Old one was was accepted by the grid.
flex1_1 = create_available_flex(user_id, METER_IDS_WITH_API_KEY[0], datetime.now()-timedelta(days=1),
                                True, True, True, True, False, False)
flex1_2 = create_available_flex(user_id, METER_IDS_WITH_API_KEY[0], datetime.now()-timedelta(days=1),
                                False, True, True, True, False, False)

# Second user: two flexibilities. Most recent one was accepted by the grid.
flex2_1 = create_available_flex(second_user_id, METER_IDS_WITH_API_KEY[1], datetime.now()-timedelta(days=1),
                                False, True, True, True, False, False)
flex2_2 = create_available_flex(second_user_id, METER_IDS_WITH_API_KEY[1], datetime.now()-timedelta(days=1),
                                True, True, True, True, False, False)

# Third user: two flexibilities not accepted by grid. One very old, and one for 2 days.
flex3_1 = create_available_flex(third_user_id, METER_IDS_WITH_API_KEY[2], datetime.now()-timedelta(days=2),
                                False, True, True, True, False, False)
flex3_2 = create_available_flex(third_user_id, METER_IDS_WITH_API_KEY[2], datetime.now(),
                                False, True, True, True, False, False)

user = get_user(user_id)
print("user with expo token:")
print(user)


