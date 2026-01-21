import json, sys
from datetime import datetime, timedelta, timezone

sys.path.append("../../..")

from energy_manager_service import generalLogger, cybergrid_ssa
from energy_manager_service.ssa.cybergrid.config import CybergridConfig


def active_power_post(start_datetime: datetime, asset: str, power_values: list):
    if power_values is None:
        generalLogger.error("Power values array must not be None.")
        return False

    # Specific Service Adapter logic #

    generalLogger.debug(f'Begin Cybergrid active power \"POST\" SSA for asset {asset} on {start_datetime}')
    generalLogger.debug(f'Power values: {power_values}')


    # ---------------------- POST request ---------------------- #

    ctv = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    day = start_datetime
    bindings = []
    for value in power_values:
        tisv = day.strftime("%Y-%m-%dT%H:%M:%SZ")
        day = day + timedelta(minutes=15)
        tiev = day.strftime("%Y-%m-%dT%H:%M:%SZ")
        bindings.append({
            "asset": f"<{asset}>",
            "ctv": f"\"{ctv}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "tisv": f"\"{tisv}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "tiev": f"\"{tiev}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
            "res_d": "\"0\"^^<http://www.w3.org/2001/XMLSchema#double>",
            "res_h": "\"0\"^^<http://www.w3.org/2001/XMLSchema#double>",
            "res_m": "\"15\"^^<http://www.w3.org/2001/XMLSchema#double>",
            "res_s": "\"0\"^^<http://www.w3.org/2001/XMLSchema#double>",
            "qapnv": f"\"{str(value)}\"^^<http://www.w3.org/2001/XMLSchema#double>"
        })

    _, post_status_code = cybergrid_ssa.ask_or_post(
        bindings=bindings,
        ki_id=cybergrid_ssa.active_power_ki_id,
        response_wait_timeout_seconds=CybergridConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=CybergridConfig.ASK_POST_SELF_HEAL_TRIES
    )

    generalLogger.debug('Cybergrid active power \"POST\" SSA finished.')


    if post_status_code != 200:
        generalLogger.error(f"React status code: {post_status_code}")
        return False
    else:
        return True
