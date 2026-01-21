import sys
from datetime import datetime, timedelta, timezone

sys.path.append("../../..")

from energy_manager_service import generalLogger, cybergrid_ssa
from energy_manager_service.ssa.cybergrid.config import CybergridConfig


def lower_limit_post(day: datetime, asset: str, power_values: list):
    if power_values is None:
        generalLogger.error("Power values array must not be None.")
        return False
    
    if len(power_values) != 96:
        generalLogger.error("Power values array must have 96 values. 15 minutes slots for an entire day.")
        return False

    # Specific Service Adapter logic #

    generalLogger.info(f'Begin Cybergrid lower limit \"POST\" SSA for asset {asset} on {day}')
    generalLogger.debug(f'Power values: {power_values}')


    # ---------------------- POST request ---------------------- #

    ctts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    day = day.replace(hour=0, minute=0, second=0)
    begts = day.strftime("%Y-%m-%dT%H:%M:%SZ")
    endts = (day + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    bindings = []
    for value in power_values:
        dpbegts = day.strftime("%Y-%m-%dT%H:%M:%SZ")
        day = day + timedelta(minutes=15)
        dpendts = day.strftime("%Y-%m-%dT%H:%M:%SZ")
        bindings.append({
            "offer": "<1>",
            "asset": f"<{asset}>",
            "begts": f"\"{begts}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "endts": f"\"{endts}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "ctts" : f"\"{ctts}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "res_m": "\"15\"^^<http://www.w3.org/2001/XMLSchema#double>",
            "organization": "\"HEMS_INESCTEC\"^^< http://www.w3.org/2001/XMLSchema#string>",
            "dpbegts":  f"\"{dpbegts}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "dpendts":  f"\"{dpendts}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "qapnv": f"\"{str(value)}\"^^<http://www.w3.org/2001/XMLSchema#double>"
        })

    react_response, react_status_code = cybergrid_ssa.ask_or_post(
        bindings=bindings,
        ki_id=cybergrid_ssa.lower_limit_ki_id,
        response_wait_timeout_seconds=CybergridConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=CybergridConfig.ASK_POST_SELF_HEAL_TRIES
    )
    if react_status_code >= 300:
        generalLogger.error(f"React status code: {react_status_code}")
        generalLogger.error(f"React response: {react_response}")

        return False

    if react_response is None:
        generalLogger.error("Empty react response")
        return False
    if "exchangeInfo" not in react_response.keys():
        generalLogger.error("No exchange info in react response")
        return False
    elif len(react_response["exchangeInfo"]) == 0:
        generalLogger.error("Empty exchange info")
        return False
    elif react_response['exchangeInfo'][0]['status'] == 'FAILED':
        generalLogger.error("Exchange info status is FAILED")
        return False

    generalLogger.debug('Cybergrid lower limit \"POST\" SSA... Finished')

    return True
