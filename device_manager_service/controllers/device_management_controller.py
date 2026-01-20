from datetime import datetime
import connexion, json, time

from device_manager_service import auth, logger, db, app, Config

from device_manager_service.models import (
    Error,
    ShiftableMachine,
    NotDisturb,
    PeriodOfDay,
    Settings,
    SettingsByDevice,
    SettingsByUser,
    UserDeviceList,
    AutomaticManagementResponseBody
)

from device_manager_service.models.db_models import DBShiftableMachine, DBNotDisturb

from device_manager_service.utils.logs import logErrorResponse, logResponse
from device_manager_service.utils.date.seconds_to_days_minutes_hours import seconds_to_days_minutes_hours
from device_manager_service.utils.database.db_interactions import delete, commit_db_changes, delete_and_commit
from device_manager_service.ssa.userkb.device_access_update_post import device_access_update_post

from device_manager_service.clients.hems_services.energy_manager import delete_recommendation


class DTEncoder(json.JSONEncoder):
    def default(self, obj):
        # 👇️ if passed in object is datetime object
        # convert it to a string
        if isinstance(obj, datetime):
            return str(obj)
        # 👇️ otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)


start = time.time()
total_time = 0

@app.route('/health')
def healthy():
    global start
    global total_time

    corId = {'X-Correlation-ID': 'health'}

    appliance = DBShiftableMachine.query.first()


    current_time = time.time()
    time_diff = current_time - start
    if time_diff >= 600:
        total_time += time_diff
        seconds_to_days_minutes_hours(total_time)
        start = current_time

    # logger.debug("Heath endpoint OK", extra=corId)

    return ''


def device_get(user_ids=None):  # noqa: E501
    """List devices per user id.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param user_ids:
    :type user_ids: List[str]
    :param authorization:
    :type authorization: str

    :rtype: List[UserDeviceList]
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed GET /device request"
    logger.info(end_text, extra=cor_id)

    if user_ids:
        logger.debug(f"User Ids: {user_ids}", extra=cor_id)
    else:
        logger.debug("No user_ids provided, defaulting to authorized user.", extra=cor_id)


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

        if user_ids:
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

        logger.info(f"Listing devices from user {auth_response}\n", extra=cor_id)

    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )

        users_list = user_ids


    # ------------------ Fetch users machines from db ------------------ #

    response = []
    for user_id in users_list:
        wp_machines = DBShiftableMachine.query.filter_by(user_id=user_id).all()

        device_list = []
        for machine in wp_machines:

            not_disturb = {
                "sunday": [],
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": []
            }

            for nd in machine.not_disturb:
                if nd.day_of_week != "{}":
                    not_disturb[nd.day_of_week].append(
                        PeriodOfDay(nd.start_timestamp, nd.end_timestamp)
                    )

            device_list.append(
                ShiftableMachine(
                    name=machine.name,
                    device_type=machine.device_type,
                    brand=machine.brand,
                    serial_number=machine.serial_number,
                    allow_hems=machine.allow_hems,
                    automatic_management=machine.automatic_management,
                    device_ssa=machine.device_ssa,
                    not_disturb=not_disturb,
                )
            )

        response.append(UserDeviceList(user_id=user_id, devices=device_list))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id


def settings_by_device_get(serial_numbers):  # noqa: E501
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed GET /settings-by-device request"
    operation_text = f"get settings for devices {serial_numbers}"
    logger.info(operation_text, extra=cor_id)


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
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
            )

        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()
        logger.debug(f"User {auth_response} has {user_machines}", extra=cor_id)

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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )



    # ----------------- Check if Device exists in user database ----------------- #

    response = []
    settings = []
    for serial_number in serial_numbers:

        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
        if device_in_db is None:

            logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
            msg = "One or more device IDs not associated with the user."
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 400, cor_id


        not_disturb = {
            "sunday": [],
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
        }

        for nd in device_in_db.not_disturb:
            if nd.day_of_week != "{}":
                not_disturb[nd.day_of_week].append(
                    PeriodOfDay(nd.start_timestamp, nd.end_timestamp)
                )

        settings.append(
            Settings(
                serial_number=device_in_db.serial_number,
                not_disturb=not_disturb,
                allow_hems=device_in_db.allow_hems,
                automatic_management=device_in_db.automatic_management,
            )
        )

        response.append(SettingsByDevice(settings))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id


def settings_by_device_post(serial_number):  # noqa: E501
    """Update not disturb settings per device.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param serial_number:
    :type serial_number: str
    :param not_disturb:
    :type not_disturb: dict | bytes
    :param authorization:
    :type authorization: str

    :rtype: NotDisturb
    """
    if connexion.request.is_json:
        not_disturb_body = NotDisturb.from_dict(
            connexion.request.get_json()
        )

    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed POST /settings-by-device request"
    operation_text = f"update settings for device {serial_number}"
    logger.info(operation_text, extra=cor_id)


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
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
            )

        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()

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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )


    # ------------------ Check if Device exists in user database ------------------ #

    device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()

    if device_in_db is None:

        logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
        msg = "One or more device IDs not associated with the user."
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return response, 400, cor_id


    # ------------------ Update device settings in database ------------------ #

    for nd in device_in_db.not_disturb:
        error_msg = "Failed to delete not disturb from database"
        response_code = delete(db.session, nd, error_msg, cor_id)
        if response_code != 200:
            return Error(error_msg), response_code, cor_id

    nds = []
    for key in not_disturb_body.sunday:
        nd = DBNotDisturb(
            day_of_week="sunday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.monday:
        nd = DBNotDisturb(
            day_of_week="monday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.tuesday:
        nd = DBNotDisturb(
            day_of_week="tuesday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.wednesday:
        nd = DBNotDisturb(
            day_of_week="wednesday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.thursday:
        nd = DBNotDisturb(
            day_of_week="thursday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.friday:
        nd = DBNotDisturb(
            day_of_week="friday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)
    for key in not_disturb_body.saturday:
        nd = DBNotDisturb(
            day_of_week="saturday",
            start_timestamp=key.start_timestamp,
            end_timestamp=key.end_timestamp,
        )
        nds.append(nd)

    device_in_db.not_disturb = nds

    error_msg = "Failed to update not disturb in database"
    response_code = commit_db_changes(db.session, error_msg, cor_id)
    if response_code != 200:
        return Error(msg), response_code, cor_id


    # ------------------ Build response object ------------------ #

    not_disturb = {
        "sunday": [],
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
    }

    for nd in device_in_db.not_disturb:
        if nd.day_of_week != "{}":
            not_disturb[nd.day_of_week].append(PeriodOfDay(
                start_timestamp=nd.start_timestamp,
                end_timestamp=nd.end_timestamp
                ))

    not_dist_obj = NotDisturb(
        sunday=not_disturb["sunday"],
        monday=not_disturb["monday"],
        tuesday=not_disturb["tuesday"],
        wednesday=not_disturb["wednesday"],
        thursday=not_disturb["thursday"],
        friday=not_disturb["friday"],
        saturday=not_disturb["saturday"],
    )

    response = Settings(
        device_type=device_in_db.device_type,
        brand=device_in_db.brand,
        serial_number=device_in_db.serial_number,
        not_disturb=not_dist_obj,
        allow_hems=device_in_db.allow_hems,
    )

    logger.info("Settings updated by the user...", extra=cor_id)
    logResponse(end_text, response, cor_id)

    return response, 200, cor_id


def settings_by_user_get(user_ids):  # noqa: E501
    """Get settings of devices per user id.

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param user_ids:
    :type user_ids: List[str]
    :param authorization:
    :type authorization: str

    :rtype: List[MachineCycleByUser]
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed Get /settings-by-user request"
    operation_text = f"get settings of devices of users {user_ids}"
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


    # ---------------------------------------- Request Logic ---------------------------------------- #

    response = []
    settings_list = []

    for user_id in users_list:
        user_machines = DBShiftableMachine.query.filter_by(user_id=user_id).all()

        for machine in user_machines:

            not_disturb = {
                "sunday": [],
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
            }

            for nd in machine.not_disturb:
                if nd.day_of_week != "{}":
                    not_disturb[nd.day_of_week].append(PeriodOfDay(
                        start_timestamp=nd.start_timestamp,
                        end_timestamp=nd.end_timestamp
                        ))

            settings_list.append(
                Settings(
                    serial_number=machine.serial_number,
                    not_disturb=not_disturb,
                    allow_hems=machine.allow_hems,
                    automatic_management=machine.automatic_management,
                )
            )

        response.append(SettingsByUser(user_id=user_id, settings=settings_list))

    logger.info(end_text, extra=cor_id)

    return response, 200, cor_id


def device_delete(serial_number, delete_type):
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed DELETE /device device request"
    logger.info("Processing DELETE /device request...", extra=cor_id)
    logger.debug(f"Device ID: {serial_number}", extra=cor_id)
    logger.debug(f"Delete Type: {delete_type}", extra=cor_id)

    
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
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
            )
        
        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()

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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )


    # ------------------ Delete device according to delete type ------------------ #

    if delete_type == "soft":
        msg = "Soft delete not allowed at the moment"
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return Error(msg), 405, cor_id
    else:
        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()

    if device_in_db is None:
        
        logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
        msg = "One or more device IDs not associated with the user."
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return response, 400, cor_id

    # Update HEMS permissions over device on spine adapter
    if Config.SPINE_USE_RECIPIENT_SELECTOR and device_in_db.device_ssa is not None:
        logger.info(f"Using Recipient selector. Updating device {serial_number} access on Spine Adapter to False...", extra=cor_id)
        
        message, response_code = device_access_update_post(serial_number, device_in_db.device_ssa, False)
        logger.info(f"SSA device access update response: {message}", extra=cor_id)
        
        if response_code != 200:
            msg = "Failed to update device access on Spine Adapter."
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, response_code, cor_id

    # if delete_type == "hard": 
    device_in_db.current_cycle_id = None  # NOTE: Fixes circular dependency error when deleting devices with an active cycle
    db.session.commit()
    error_msg = f"Failed to delete device {serial_number} from database."
    response_code = delete_and_commit(db.session, device_in_db, error_msg, cor_id)
    if response_code != 200:
        return Error(error_msg), response_code, cor_id
    else:
        for cycle in device_in_db.washing_cycles:
            # Delete flex recommendation associated with cycle 
            del_response, del_status_code = delete_recommendation(
                serial_number, cycle.sequence_id
            )
            if 400 <= del_status_code < 500:
                logger.warning(
                    f"Failed to delete recommendation from Energy Manager Service: " \
                    f"{del_response['error']}",
                    extra=cor_id
                )

    logger.info(f"Device {serial_number} was HARD deleted!", extra=cor_id)
    logger.info(f"{end_text}\n", extra=cor_id)

    return serial_number, response_code, cor_id


def device_settings_set_automatic_management_post(serial_number):  # noqa: E501
    """Set automatic management of settings per device.

     # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param serial_number: 
    :type serial_number: str
    :param authorization: 
    :type authorization: str

    :rtype: AutomaticManagementResponseBody
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed POST /device/settings/set-automatic-management device request"
    logger.info("Processing POST /device/settings/set-automatic-management request...", extra=cor_id)
    logger.debug(f"Device ID: {serial_number}", extra=cor_id)

    
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
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
            )
        
        user_machines = DBShiftableMachine.query.filter_by(user_id=auth_response).all()

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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )
    
    
    # ------------------ Set automatic management flag accordingly ------------------ #
    
    device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
    
    if device_in_db is None:
        logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
        msg = "One or more device IDs not associated with the user."
        response = Error(msg)
        status_code = 400

        logErrorResponse(msg, end_text, response, cor_id)
    
    else:
        if device_in_db.automatic_management is True:
            device_in_db.automatic_management = False
            response = AutomaticManagementResponseBody(False)
            
        else:
            device_in_db.automatic_management = True
            response = AutomaticManagementResponseBody(True)
        db.session.commit()
        status_code = 200

        logger.info(f"Device {serial_number} automatic management flag was updated to {device_in_db.automatic_management}!", extra=cor_id)
    
    
    return response, status_code, cor_id