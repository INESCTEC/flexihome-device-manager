import json, traceback
from datetime import datetime, timedelta, timezone

from energy_manager_service import db, logger
from energy_manager_service.models.database.energy_manager_db import TableScheduleHistorical


def export_json_to_db(request_type, endpoint_name, dict_obj, user_id, cor_id): 
    
    json_obj = json.dumps(
        dict_obj, 
        default=lambda o: o.__dict__, 
        )
    try:
        tb = TableScheduleHistorical(
            user_id            = user_id,
            request_type       = request_type,
            info_name          = endpoint_name,
            # start_date         = Config.START_DAY_AHEAD_UTC,
            start_date         = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0),
            datetime_requested = datetime.now(),
            json_obj           = json_obj
        )

        db.session.add(tb)
        db.session.commit()     
        db.session.close()

        logger.debug('Historical data was stored.', extra=cor_id)
        
    except Exception as ErrorCodes: 
        log_message = "Export info to DB %s "%(str(ErrorCodes).replace("'",""))
        logger.error(log_message, extra=cor_id)
        traceback.print_exc()
        
        return str(401)
    
    return True