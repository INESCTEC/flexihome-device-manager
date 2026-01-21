import sys, uuid, requests
from time import sleep

sys.path.append("..")

from config import Config, generalLogger
from account_get_all_users import get_all_users


user_list, status_code = get_all_users()

for user in user_list:
    
    headers = {
        "X-Correlation-ID": str(uuid.uuid4())
    }
    query_parameters = {
        "user_id": user
    }
    
    response = requests.post(
        f"{Config.HOST_ENERGYMANAGER}/flexibility/available",
        headers=headers,
        params=query_parameters
    )

    sleep(Config.SECONDS_BETWEEN_REQUESTS)  # Sleep for 10 seconds to avoid overloading the KE and cause gateway timeouts

    if response.status_code >= 300:
        generalLogger.warning(f"Error building available flexibility for user {user}")
        generalLogger.debug(response.content)
        continue
    else:
        try:
            generalLogger.debug(response.content)
            response_body = response.json()
        except Exception as e:
            generalLogger.warning(f"Error parsing response body: {repr(e)}")
            continue
        
        generalLogger.debug(response_body)
        
        generalLogger.info(f"Successfully built available flexibility for user {user}")
