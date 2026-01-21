from datetime import datetime, timezone
import connexion
import json
from datetime import datetime

from device_manager_service import util, auth, logger

from device_manager_service.models import (
    Error,
    MachineCycleByUser,
    MachineCycleByDevice
)

from device_manager_service.models.db_models import DBShiftableMachine

from device_manager_service.utils.models.deserialize import deserialize_washing_cycle
from device_manager_service.utils.logs import logErrorResponse



class DTEncoder(json.JSONEncoder):
    def default(self, obj):
        # 👇️ if passed in object is datetime object
        # convert it to a string
        if isinstance(obj, datetime):
            return str(obj)
        # 👇️ otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)



def schedule_cycle_by_device_get(serial_numbers, start_timestamp=None, end_timestamp=None, is_cycle_optimized=None):
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed GET /schedule-cycle-by-device request"
    logger.info("Starting GET /schedule-cycle-by-device requests...\n", extra=cor_id)
    
    logger.debug(f"Device Ids: {serial_numbers}", extra=cor_id)

    if start_timestamp is None and end_timestamp is None:
        logger.debug("Retrieving ALL schedules from devices on the list", extra=cor_id)
    else:
        logger.debug(f"Start DateTime: {start_timestamp}", extra=cor_id)
        logger.debug(f"End DateTime: {end_timestamp}", extra=cor_id)
    
    if is_cycle_optimized:
        logger.debug(f"Looking for optimized cycles? {is_cycle_optimized}\n", extra=cor_id)
        # Convert string query parameter to boolean
        if is_cycle_optimized == "false":
            is_cycle_optimized = False
        else:
            is_cycle_optimized = True
    else:
        logger.debug(f"Looking for ALL cycles, optimized or not\n", extra=cor_id)

    # ----------------- Define user permissions ----------------- #

    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if auth_code != 200:
        
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        
        logErrorResponse(msg, end_text, response, cor_id)
        return response, auth_code, cor_id
    
    elif auth_code == 200 and auth_response is not None:
        
        logger.info(
            f"User {auth_response} accessing from API Gateway...\n",
            extra=cor_id
            )
        
        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()

        for serial_number in serial_numbers:
            if serial_number not in [machine.serial_number for machine in user_machines]:

                logger.warning(
                    f"User {auth_response} tried to access other users devices!",
                    extra=cor_id
                    )

                msg = "Unauthorized Action!"
                response = Error(msg)

                logErrorResponse(msg, end_text, response, cor_id)
                return Error(msg), 403, cor_id
        
    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...\n",
            extra=cor_id
            )

    

    if start_timestamp:
        start_dt = util.deserialize_datetime(start_timestamp)
        start_dt_utc = start_dt.replace(tzinfo=timezone.utc)
    if end_timestamp:
        end_dt = util.deserialize_datetime(end_timestamp)
        end_dt_utc = end_dt.replace(tzinfo=timezone.utc)


    # --------------------- Check if Device exists in user database --------------------- #

    response = []
    for serial_number in serial_numbers:
        cycles_pool = []
        
        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
        if device_in_db is None:
        
            logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
            msg = "One or more device IDs not associated with the user."
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 400, cor_id


        # --------------------- Build request response object --------------------- #

        cycles = deserialize_washing_cycle(device_in_db)

        for cycle in cycles:
            
            logger.info(
                f"Cycle {cycle.sequence_id} of device {device_in_db.serial_number}",
                extra=cor_id
                )

            # Enforce "is_cycle_optimized" query parameter
            if is_cycle_optimized is None:
                logger.debug("'is_cycle_optimized' query parameter not set", extra=cor_id)

            elif is_cycle_optimized and cycle.is_optimized:
                logger.debug(
                    "Cycle IS optimized in accordance with 'is_cycle_optimized' query parameter",
                    extra=cor_id
                    )

            elif is_cycle_optimized is False and cycle.is_optimized is False:
                logger.debug(
                    "Cycle is NOT optimized in accordance with 'is_cycle_optimized' query parameter",
                    extra=cor_id
                    )
            else:
                logger.debug(
                    "Cycle does not match 'is_cycle_optimized' query parameter requirements\n" \
                    f"'is_cycle_optimized': {is_cycle_optimized}\n" \
                    f"Cycle is_optimized? {cycle.is_optimized}\n",
                    extra=cor_id
                    )
                continue
            

            cycle_start_timestamp_utc = cycle.scheduled_start_time.replace(tzinfo=timezone.utc)

            if start_timestamp:
    
                if cycle_start_timestamp_utc.timestamp() >= start_dt_utc.timestamp():
                    
                    logger.debug(
                        f"Cycle start time is after {start_dt_utc}", 
                        extra=cor_id
                        )

                    if end_timestamp:
                        
                        if cycle_start_timestamp_utc.timestamp() <= end_dt_utc.timestamp():

                            logger.debug(
                                f"Cycle start time is before {end_dt_utc}", extra=cor_id
                            )
                            logger.info(
                                f"Query found: Cycle {cycle.sequence_id} " \
                                f"of device {device_in_db.serial_number}",
                                extra=cor_id
                            )

                            cycles_pool.append(cycle)
                    
                    else:
                        logger.info(
                            f"Query found: Cycle {cycle.sequence_id} " \
                            f"of device {device_in_db.serial_number}",
                            extra=cor_id
                        )
                        cycles_pool.append(cycle)
            
            elif end_timestamp:

                if cycle_start_timestamp_utc.timestamp() <= end_dt_utc.timestamp():

                    logger.debug(
                        f"Cycle start time is before {end_dt_utc}", 
                        extra=cor_id
                        )
                    logger.info(
                        f"Query found: Cycle {cycle.sequence_id} " \
                        f"of device {device_in_db.serial_number}",
                        extra=cor_id
                    )
                        
                    cycles_pool.append(cycle)

            else:
                logger.info(
                    f"Query found: Cycle {cycle.sequence_id} " \
                    f"of device {device_in_db.serial_number}",
                    extra=cor_id
                )
                cycles_pool.append(cycle)

        response.append(MachineCycleByDevice(serial_number=device_in_db.serial_number,cycles=cycles_pool))


    logger.info(f"{end_text}\n", extra=cor_id)

    return response, 200, cor_id


def schedule_cycle_by_user_get(user_ids, start_timestamp=None, end_timestamp=None, is_cycle_optimized=None):
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed Get /schedule-cycle-by-user request"
    logger.info(f"GET /schedule-cycle-by-user with user ids: {user_ids}", extra=cor_id)

    if start_timestamp is None and end_timestamp is None:
        logger.debug("Retrieving ALL schedules from devices on the list", extra=cor_id)
    else:
        logger.debug(f"Start DateTime: {start_timestamp}", extra=cor_id)
        logger.debug(f"End DateTime: {end_timestamp}", extra=cor_id)
    
    if is_cycle_optimized:
        logger.debug(f"Looking for optimized cycles? {is_cycle_optimized}\n", extra=cor_id)
        # Convert string query parameter to boolean
        if is_cycle_optimized == "false":
            is_cycle_optimized = False
        else:
            is_cycle_optimized = True
    else:
        logger.debug(f"Looking for ALL cycles, optimized or not\n", extra=cor_id)


    # ----------------- Verify request permissions ----------------- #

    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    users_list = []
    if auth_code != 200:
        
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        
        logErrorResponse(msg, end_text, response, cor_id)
        return response, auth_code, cor_id
    
    
    elif auth_code == 200 and auth_response is not None:
        
        logger.info(
            f"User {auth_response} accessing from API Gateway...\n",
            extra=cor_id
            )
        

        if len(user_ids) > 1:
            logger.error(
                f"User {auth_response} tried to access other users accounts.\n",
                extra=cor_id
                )
            msg = "Unauthorized action!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 403, cor_id
        

        if user_ids[0] != auth_response:
            logger.error(
                f"User {auth_response} trying to access different user devices ({user_ids[0]})",
                extra=cor_id
                )
            
            msg = "Unauthorized action!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 403, cor_id
        
        users_list = [auth_response]

    
    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...\n",
            extra=cor_id
            )
        
        users_list = user_ids

    

    if start_timestamp:
        start_dt = util.deserialize_datetime(start_timestamp)
        start_dt_utc = start_dt.replace(tzinfo=timezone.utc)
    if end_timestamp:
        end_dt = util.deserialize_datetime(end_timestamp)
        end_dt_utc = end_dt.replace(tzinfo=timezone.utc)

    logger.debug(
        f"Get schedule cycle between {start_timestamp} and {end_timestamp}\n",
        extra=cor_id
        )

    
    # --------------------- Build request response object --------------------- #

    response = []
    for user_id in users_list:
        
        scheduled_cycles = []
        user_machines = DBShiftableMachine.query.filter_by(user_id=user_id).all()
        logger.debug(f"User {user_id} machines in db:\n{user_machines}\n", extra=cor_id)

        for machine in user_machines:
            cycles_pool = []
            cycles = deserialize_washing_cycle(machine)

            for cycle in cycles:

                logger.debug(
                    f"Cycle {cycle.sequence_id} of device {machine.serial_number}",
                    extra=cor_id
                    )

                # Enforce "is_cycle_optimized" query parameter
                if is_cycle_optimized is None:
                    logger.debug("'is_cycle_optimized' query parameter not set", extra=cor_id)

                elif is_cycle_optimized and cycle.is_optimized:
                    logger.debug(
                        "Cycle IS optimized in accordance with 'is_cycle_optimized' query parameter",
                        extra=cor_id
                        )

                elif is_cycle_optimized is False and cycle.is_optimized is False:
                    logger.debug(
                        "Cycle is NOT optimized in accordance with 'is_cycle_optimized' query parameter",
                        extra=cor_id
                        )
                else:
                    logger.debug(
                        "Cycle does not match 'is_cycle_optimized' query parameter requirements\n" \
                        f"'is_cycle_optimized': {is_cycle_optimized}\n" \
                        f"Cycle is_optimized? {cycle.is_optimized}\n",
                        extra=cor_id
                        )
                    continue
            
            
                if start_timestamp:

                    cycle_start_timestamp_utc = cycle.scheduled_start_time.replace(
                        tzinfo=timezone.utc
                        )
        
                    if cycle_start_timestamp_utc.timestamp() >= start_dt_utc.timestamp():
                        
                        logger.debug(
                            f"Cycle start time is after {start_dt_utc}", 
                            extra=cor_id
                            )
                        
                        if end_timestamp:
                        
                            if cycle_start_timestamp_utc.timestamp() <= end_dt_utc.timestamp():

                                logger.debug(
                                    f"Cycle start time is before {end_dt_utc}", extra=cor_id
                                )
                                logger.info(
                                    f"Query found: Cycle {cycle.sequence_id} " \
                                    f"of device {machine.serial_number}",
                                    extra=cor_id
                                )

                                cycles_pool.append(cycle)
                        
                        else:
                            logger.info(
                                f"Query found: Cycle {cycle.sequence_id} " \
                                f"of device {machine.serial_number}",
                                extra=cor_id
                            )
                            cycles_pool.append(cycle)
                
                elif end_timestamp:
                    
                    if cycle_start_timestamp_utc.timestamp() <= end_dt_utc.timestamp():

                        logger.debug(
                            f"Cycle start time is before {end_dt_utc}", 
                            extra=cor_id
                            )
                        logger.info(
                            f"Query found: Cycle {cycle.sequence_id} " \
                            f"of device {machine.serial_number}",
                            extra=cor_id
                        )

                        cycles_pool.append(cycle)
                
                else:
                    logger.info(
                        f"Query found: Cycle {cycle.sequence_id} " \
                        f"of device {machine.serial_number}",
                        extra=cor_id
                    )
                    cycles_pool.append(cycle)

            scheduled_cycles.append(MachineCycleByDevice(serial_number=machine.serial_number,cycles=cycles_pool))

        response.append(MachineCycleByUser(user_id=user_id, cycles=scheduled_cycles))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id