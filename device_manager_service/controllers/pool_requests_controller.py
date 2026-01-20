from datetime import datetime, timedelta
import connexion
import time
import json
from datetime import datetime

from device_manager_service import auth, logger

from device_manager_service.models import (
    Error,
    Pool,
    PoolByDevice,
    PoolByUser
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



# TODO: USING THIS FUNCTION AS AN EXAMPLE, DIVIDE INTO SMALLER FUNCTIONS THAT CAN BE REUSED IN OTHER REQUESTS
# TODO: POSTMAN TESTS WITH EVERY CASE IN THIS FUNCTION (user not authorized, user has no devices, etc.)
def pool_by_device_get(serial_numbers):  # noqa: E501
    """Get scheduled pool per device ids.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param serial_numbers:
    :type serial_numbers: List[str]
    :param authorization:
    :type authorization: str

    :rtype: List[PoolByUser]
    """

    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed GET /pool-by-device request"
    operation_text = f"get scheduled pool from devices {serial_numbers}"
    logger.debug(operation_text, extra=cor_id)

    # Flag to indicate if request has an error
    request_error = False
    request_status_code = 500


    # ----------------- Define user permissions ----------------- #

    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if auth_code != 200:
        
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        
        response = Error(msg)
        request_status_code = auth_code
        request_error = True
        
        logErrorResponse(msg, end_text, response, cor_id)
        # return response, auth_code, cor_id
    
    elif auth_code == 200 and auth_response is not None:
        
        logger.info(
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
            )
        
        # LOG IF THERE IS ANY SOFT DELETED DEVICES 
        # user_deleted_machines = DBShiftableMachine.query.filter_by(user_id=auth_response, deleted=True).all()
        # if len(user_deleted_machines) > 0:
        #     for machine in user_deleted_machines:
        #         logger.debug(
        #             f"User '{auth_response}' has a deleted device with id '{machine.serial_number}'",
        #             extra=cor_id
        #         )
            
        #     logger.info(
        #         f"User '{auth_response}' has {len(user_deleted_machines)} deleted devices",
        #         extra=cor_id
        #     )

        # else:
        #     logger.info(f"User '{auth_response}' has no deleted devices", extra=cor_id)


        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()
        if len(user_machines) == 0:
            logger.warning(f"User {auth_response} has no devices associated", extra=cor_id)

            msg = "User's devices not found"

            response = Error(msg)
            request_status_code = 404
            request_error = True
        
        else:

            for serial_number in serial_numbers:
                if serial_number not in [machine.serial_number for machine in user_machines]:

                    logger.warning(
                        f"User {auth_response} tried to access other users devices!",
                        extra=cor_id
                        )

                    msg = "Unauthorized Action!"
                    
                    response = Error(msg)
                    request_status_code = 403
                    request_error = True

                    logErrorResponse(msg, end_text, response, cor_id)
                    # return response, 403, cor_id
        
    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
        )


    # ----------------- Check if Device exists in user database ----------------- #
    
    for serial_number in serial_numbers:
    
        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
        if device_in_db is None:
    
            logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
            msg = "One or more device IDs not associated with the user."
            
            response = Error(msg)
            request_status_code = 400
            request_error = True

            logErrorResponse(msg, end_text, response, cor_id)
            # return response, 400, cor_id
        

    # ------------------------ Request logic ------------------------ #
    
    if request_error == False:
        response = []
        day_ahead = datetime.now() + timedelta(days=1)
        
        for serial_number in serial_numbers:
            pool = []
            
            cycles = deserialize_washing_cycle(device_in_db)
            cycles = [
                cycle for cycle in cycles 
                if cycle.scheduled_start_time.day == day_ahead.day and
                cycle.scheduled_start_time.month == day_ahead.month and
                cycle.scheduled_start_time.year == day_ahead.year
                ]

            if len(cycles) > 0:
                pool.append(Pool(
                    serial_number=device_in_db.serial_number,
                    device_type=device_in_db.device_type,
                    cycles_in_pool=cycles
                    ))

            if len(pool) > 0:
                response.append(PoolByDevice(pool=pool))
        
        request_status_code = 200


    logger.info(end_text, extra=cor_id)

    return response, request_status_code, cor_id


def pool_by_user_get(user_ids):  # noqa: E501
    """Get scheduled pools per user ids.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param user_ids:
    :type user_ids: List[str]
    :param authorization:
    :type authorization: str

    :rtype: List[PoolByUser]
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed Get /pool-by-user request"
    logger.info(end_text, extra=cor_id)
    logger.debug(f"User Ids: {user_ids}", extra=cor_id)

   
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
            f"User {auth_response} accessing from API Gateway...",
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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )
        
        users_list = user_ids

    
    # ----------------- Fetch cycles from devices of users ----------------- #

    day_ahead = datetime.now() + timedelta(days=1)
    response = []

    for user_id in users_list:
        wp_machines = DBShiftableMachine.query.filter_by(user_id=user_id).all()

        pool = []
        for machine in wp_machines:
            
            cycles = deserialize_washing_cycle(machine)
            cycles = [
                cycle for cycle in cycles
                if cycle.scheduled_start_time.day == day_ahead.day and
                cycle.scheduled_start_time.month == day_ahead.month and
                cycle.scheduled_start_time.year == day_ahead.year
            ]

            if len(cycles) > 0:
                pool.append(Pool(
                    serial_number=machine.serial_number,
                    device_type=machine.device_type, 
                    cycles_in_pool=cycles
                    ))

        if len(pool) > 0:
            response.append(PoolByUser(user_id=user_id, pool=pool))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id

def perfect_pool_by_user_get(user_ids, start_date, end_date):  # noqa: E501
    """Get scheduled pools per user ids.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param user_ids:
    :type user_ids: List[str]
    :param authorization:
    :type authorization: str

    :rtype: List[PoolByUser]
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed Get /pool-by-user request"
    operation_text = f"get scheduled pools from devices of users {user_ids}"
    logger.info(operation_text, extra=cor_id)


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
            f"User {auth_response} accessing from API Gateway...",
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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )
        
        users_list = user_ids


    # ----------------- Parse timestamps into date objects ----------------- #

    start_date_object = datetime.strptime(start_date, "%Y-%m-%d").date()
    start_timestamp = time.mktime(
        start_date_object.timetuple()
    )  # 00:00:00 of start_date

    end_date_object = datetime.strptime(end_date, "%Y-%m-%d").date()
    end_timestamp = time.mktime(
        (end_date_object + timedelta(days=1)).timetuple()
    )  # 00:00:00 of the day after end_date

    response = []
    for user_id in users_list:
        wp_machines = DBShiftableMachine.query.filter_by(user_id=user_id).all()

        pool = []
        for machine in wp_machines:
            cycles_pool = []

            cycles = deserialize_washing_cycle(machine)
            for cycle in cycles:
                cycle_scheduled_start_time = time.mktime(
                    cycle.scheduled_start_time.timetuple()
                )

                if (
                    cycle_scheduled_start_time >= start_timestamp
                    and cycle_scheduled_start_time < end_timestamp
                ):
                    cycles_pool.append(cycle)

            pool.append(Pool(
                serial_number=machine.serial_number,
                device_type=machine.device_type,
                cycles_in_pool=cycles_pool
                ))

        response.append(PoolByUser(user_id=user_id, pool=pool))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id
