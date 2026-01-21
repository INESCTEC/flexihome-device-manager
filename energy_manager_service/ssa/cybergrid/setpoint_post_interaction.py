# THIS IS A TEST INTERACTION
# THE REAL SETPOINT INTERACTION IS MADE BY THE AGGREGATOR

import json
from datetime import datetime, timedelta, timezone

from energy_manager_service import generalLogger, cybergrid_ssa
from energy_manager_service.ssa.cybergrid.config import CybergridConfig

def setpoint_post(asset):
    # Specific Service Adapter logic #

    generalLogger.debug(f'Begin Cybergrid setpoint \"POST\" SSA for asset {asset}')


    # ---------------------- POST request ---------------------- #

    start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    end_date = start_date + timedelta(days=1)
    next_date = start_date + timedelta(minutes=15)

    # asset = 'NLV_CLIENT_1706'
    # asset = 'NLV_CLIENT_655'

    bindings = [{
        'tiev': f"\"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
        'qapv': '"10.000"^^<http://www.w3.org/2001/XMLSchema#double>',
        'ctv': f"\"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>",
        'dp': '<http://api.3e.com/devices/e964ddc5-f6bf-44eb-82df-56b6a7e535b9/2021-04-29T15:00:00Z>',
        'asset': f'<{asset}>',
        'tisv': f"\"{next_date.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^<http://www.w3.org/2001/XMLSchema#dateTimeStamp>"
    }]

    react_response, react_status_code = cybergrid_ssa.ask_or_post(
        bindings=bindings,
        ki_id=cybergrid_ssa.setpoint_post_ki_id,
        response_wait_timeout_seconds=CybergridConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=CybergridConfig.ASK_POST_SELF_HEAL_TRIES
    )
    if react_status_code >= 300:
        return False


    generalLogger.debug('Cybergrid setpoint \"POST\" SSA finished.')

    return True