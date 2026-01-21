import sys, traceback, uuid
from datetime import datetime, timedelta
from typing import List

sys.path.append('../../..')

from energy_manager_service import generalLogger, Config

from energy_manager_service.clients.hems_services.account_manager import get_all_users, get_user
from energy_manager_service.clients.hems_services.forecast import get_forecast
from energy_manager_service.ssa.cybergrid.baseline_post_interaction import baseline_post


INFLUX_DB_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# List all user ids
response, status_code = get_all_users()
generalLogger.info(f'AccountService (/user-list): response {response}')
generalLogger.info(f'AccountService (/user-list): status_code {status_code}')

start_date = datetime.now().replace(second=0, minute=0, hour=0) + timedelta(days=Config.BASELINE_DAYS_AHEAD)


# Loop users
for user in response:
    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    user_profile, status_code = get_user(user, cor_id=cor_id)
    if status_code < 300:

        # Get Forecast data for the next day
        response, status = get_forecast(installation_code=f'{user}_consumption', start_date=start_date, x_correlation_id=cor_id)

        if status < 300:
            generalLogger.info("Get forecast... OK")

            # Send meter data to Cybergrid (baseline SSA)
            if response is not None:
                if len(response) != 0:

                    installation_data = response['data']
                    if len(installation_data) != 0:
                        installation_values = installation_data[0]['values']
                        if len(installation_values) == 24:
                            power_consumed : List[float] = [round(record['value_p'], 2) for record in installation_values]

                            try:
                                status = baseline_post(day=start_date, asset=user_profile['meter_id'], power_values=power_consumed)
                                if status:
                                    generalLogger.info("Baseline POST interaction... OK")
                                else:
                                    generalLogger.error("Baseline POST interaction... FAILED")
                            except Exception as e:
                                generalLogger.error(f"Baseline POST interaction failed with exception: {repr(e)}")
                                traceback.print_exc()
                        
                        else:
                            generalLogger.error("Forecast array has inconsistent length (!=24)")
                    else:
                        generalLogger.error("No data found in forecast response")
                else:
                    generalLogger.error("No records found in influxdb")
            else:
                generalLogger.error("No result from influxdb")
        else:
            generalLogger.error(f"Get forecast... FAILED (status code: {status})")
    else:
        generalLogger.error(f"Get user... FAILED (status code: {status_code})")

