import sys, uuid, requests, traceback

sys.path.append("..")

from energy_manager_service import Config, generalLogger
from energy_manager_service.clients.hems_services.account_manager import get_all_users, get_user

from energy_manager_service.ssa.cybergrid.setpoint_post_interaction import setpoint_post

user_list, status_code = get_all_users()

# user_list = ["mev7l28nv1", "oc72wghbce"]

for user in user_list:

    user_profile, get_user_status_code = get_user(user)
    if get_user_status_code < 300:
        user_profile = user_profile[0]

        headers = {
            "X-Correlation-ID": str(uuid.uuid4())
        }
        query_parameters = {
            "user_id": user
        }
        
        response = requests.get(
            f"{Config.HOST_ENERGYMANAGER}/flexibility/available",
            headers=headers,
            params=query_parameters
        )
        if response.status_code < 300:
            try:
                # generalLogger.debug(response.content)
                response_body = response.json()
            except Exception as e:
                generalLogger.warning(f"Error parsing response body: {repr(e)}")
                continue
            
            # generalLogger.debug(response_body)
            generalLogger.info(f"Successfully built available flexibility for user {user}")

            try:
                status = setpoint_post(asset=user_profile['meter_id'])
                if status:
                    generalLogger.info("Setpoint POST interaction... OK")
                else:
                    generalLogger.error("Setpoint POST interaction... FAILED")
            except Exception as e:
                generalLogger.error(f"Setpoint POST interaction failed with exception: {repr(e)}")
                traceback.print_exc()
        
        else:
            generalLogger.warning(f"Error building available flexibility for user {user}")
    else:
        generalLogger.warning(f"User profile for user {user} returned error code {get_user_status_code}")
