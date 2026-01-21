import sys, influxdb_client, traceback
from datetime import datetime, timedelta, timezone
from typing import List

sys.path.append('../../..')

from energy_manager_service import generalLogger, Config

from energy_manager_service.clients.hems_services.account_manager import list_dongles, get_user, get_all_users
from energy_manager_service.ssa.cybergrid.active_power_post_interaction import active_power_post


INFLUX_DB_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Instantiate influxdb client and query api
client = influxdb_client.InfluxDBClient(
    url=Config.INFLUX_URL,
    token=Config.INFLUX_TOKEN,
    org=Config.INFLUX_ORG
)
query_api = client.query_api()

start_datetime = datetime.now(timezone.utc).replace(second=0) - timedelta(minutes=1)
formatted_start_date = start_datetime.strftime(INFLUX_DB_DATE_FORMAT)
formatted_end_date = (start_datetime + timedelta(minutes=1)).strftime(INFLUX_DB_DATE_FORMAT)



# List all users meter ids
response, _ = list_dongles()
user_list, _ = get_all_users()

# Loop users
for user in response:
    user_list.remove(user['user_id'])
    
    # Get user info
    user_profile, status_code = get_user(user['user_id'])
    
    if status_code < 300:
        user_profile = user_profile[0]

        # Get meter data from influx.
        query = f"""from(bucket: "{Config.INFLUX_BUCKET}") 
        |> range(start: {formatted_start_date}, stop: {formatted_end_date}) 
        |> filter(fn: (r) => r["_measurement"] == "{user['api_key']}") 
        |> filter(fn: (r) => r["_field"] == "powerImported")
        |> last()"""

        generalLogger.debug(f"Query: {query}\n")

        result = query_api.query(query=query)
        generalLogger.info("Querying dongle from influxdb... OK")
        generalLogger.debug(f"Result: {result}\n")

        # Send meter data to Cybergrid (Active power SSA)
        if result is not None:
            if len(result) != 0:
                records = result[0].records

                power_consumed : List[float] = [round(record.get_value(), 2) for record in records]
                try:
                    status = active_power_post(start_datetime=start_datetime, asset=user_profile['meter_id'], power_values=power_consumed)
                    if status:
                        generalLogger.info("Active power POST interaction... OK")
                    else:
                        generalLogger.error("Active power POST interaction... FAILED")
                except Exception as e:
                    generalLogger.error(f"Active power POST interaction failed with exception: {repr(e)}")
                    traceback.print_exc()

            else:
                generalLogger.error("No records found in influxdb")
                generalLogger.warning(f"Adding {user['user_id']} to user list to send zero values later.")
                user_list.append(user['user_id'])
        else:
            generalLogger.error("No result from influxdb")
            generalLogger.warning(f"Adding {user['user_id']} to user list to send zero values later.")
            user_list.append(user['user_id'])
    else:
        generalLogger.error(f"No user profile found for user {user['user_id']}")


## SEND ZERO VALUES TO REMAINING USERS
generalLogger.info("Sending zero values to remaining users")
generalLogger.debug(f"Remaining users: {user_list}")
power_consumed_zeros = [0.0]
for user_id in user_list:
    
    # Get user info
    user_profile, status_code = get_user(user_id)
    if status_code < 300:
        user_profile = user_profile[0]
    
        try:
            active_power_post(start_datetime=start_datetime, asset=user_profile['meter_id'], power_values=power_consumed_zeros)
        except Exception as e:
            generalLogger.error(f"Active power POST interaction failed with exception: {repr(e)}")
            traceback.print_exc()
    else:
        generalLogger.error(f"No user profile found for user {user['user_id']}")
