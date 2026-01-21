from datetime import datetime, timedelta
from time import sleep
import connexion, json, uuid, requests, os

from flask import redirect, request, session

from device_manager_service import Config, logger, db, auth, app

from device_manager_service.models import (
    Error,
    ShiftableMachine,
    NotDisturb,
    DelaysStatus,
    DelaysByCycleRequestBody,
    AllowHemsRequestBody
)

from device_manager_service.models.db_models import (
    DBShiftableMachine,
    DBShiftableCycle
)

from device_manager_service.ssa.whirlpool.wp_appliances_ask import wp_appliances_ask
from device_manager_service.ssa.whirlpool.wp_register_ask import wp_register_ask
from device_manager_service.ssa.whirlpool.wp_delay_post import wp_delay_post
from device_manager_service.ssa.bosch_miele.bsh_delay_post import bsh_delay_post
from device_manager_service.ssa.bosch_miele.device_metadata_ask import bsh_appliances_metadata_ask
from device_manager_service.ssa.userkb.device_access_update_post import device_access_update_post

from device_manager_service.utils.logs import logErrorResponse
from device_manager_service.utils.database.db_interactions import add_row_to_table, commit_db_changes

from device_manager_service.clients.hems_services.energy_manager import post_flexibility_recommendations_accept


class DTEncoder(json.JSONEncoder):
    def default(self, obj):
        # 👇️ if passed in object is datetime object
        # convert it to a string
        if isinstance(obj, datetime):
            return str(obj)
        # 👇️ otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)



def request_delay_by_cycle_post(user_id, recommendation_id=None):
    if connexion.request.is_json:
        delays_by_cycle_request_body = [DelaysByCycleRequestBody.from_dict(d) for d in connexion.request.get_json()]

    connection_headers = connexion.request.headers
    cor_id = {"X-Correlation-ID": connection_headers["X-Correlation-ID"]}

    end_text = "Processed POST /request-delay-by-cycle"

    logger.info("Starting request /request-delay-by-cycle", extra=cor_id)
    logger.debug(f"User Id: {user_id}", extra=cor_id)
    logger.debug(f"Recommendation ID: {recommendation_id}", extra=cor_id)
    for cycle in delays_by_cycle_request_body:
        logger.debug(cycle, extra=cor_id)


    # ------------------------------ Verify request permissions ------------------------------ #

    auth_response, auth_code = auth.verify_basic_authorization(connection_headers)

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
        
        if user_id != auth_response:
            logger.error(
                f"User {auth_response} trying to access different user devices ({user_id})",
                extra=cor_id
                )
            
            msg = "Unauthorized action!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 403, cor_id
            

    else:
        logger.info(
            f"Only internal requests are allowed to make delays. Proceeding...",
            extra=cor_id
            )


    operation_text = f"request delay for devices of user {user_id}"
    logger.info(operation_text, extra=cor_id)


    # ------------------------------ Cycles belong to user? ------------------------------ #

    for delay_by_cyle in delays_by_cycle_request_body:
        sequence_id = delay_by_cyle.sequence_id
        serial_number = delay_by_cyle.serial_number

        logger.debug(f"Device ID {serial_number}", extra=cor_id)
        logger.debug(f"Cycle ID {sequence_id}", extra=cor_id)
        
        cycle_in_db = db.session.query(DBShiftableCycle).join(
            DBShiftableMachine, DBShiftableCycle.shiftable_machine_id == DBShiftableMachine.id
        ).filter(
            DBShiftableMachine.serial_number == serial_number
        ).filter(
            DBShiftableCycle.sequence_id == sequence_id
        ).first()
        
        # Cycle does not exist
        if cycle_in_db is None:
            logger.error(f"Cycle {sequence_id} does not exist in database", extra=cor_id)

            msg = "One or more cycles do not exist"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 404, cor_id
        
        logger.info(f"Cycle in DB: {cycle_in_db}\n", extra=cor_id)


        device_in_db = DBShiftableMachine.query.filter_by(
            serial_number=serial_number
        ).first()

        logger.debug(
            f"Cycle ID {sequence_id} found on device {device_in_db.serial_number}" \
            f"from user {device_in_db.user_id}",
            extra=cor_id
            )

        # Cycle exists but it belongs to another user
        if device_in_db.user_id != user_id:
            logger.error(
                f"You're trying to delay cycle {cycle_in_db.sequence_id} " \
                f"which belongs to user {device_in_db.user_id}" \
                f"while delaying cycle from user {user_id}",
                extra=cor_id
                )
            
            msg = "Cycles in request body MUST belong to the user in the query paramter"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 400, cor_id


    # ------------------------------ Delay ------------------------------ #

    response = []
    for delay_by_cyle in delays_by_cycle_request_body:
        sequence_id = delay_by_cyle.sequence_id
        serial_number = delay_by_cyle.serial_number
        new_start_time = delay_by_cyle.new_start_time - timedelta(hours=1)

        logger.info(f"Delaying cycle: {sequence_id}", extra=cor_id)
        logger.debug(f"Device ID {serial_number}", extra=cor_id)
        logger.debug(f"New start time: {new_start_time}", extra=cor_id)

        device_in_db = DBShiftableMachine.query.filter_by(
            serial_number=serial_number
        ).first()


        if device_in_db.brand.lower() in ["bosch", "miele"]:

            logger.info("Bosch Delay!\n", extra=cor_id)

            # NOTE: FOR SPINE SSA PURPOSES
            base_url = "http://example.org/spine-ssa/devices/"
            power_sequence = f"<{base_url}{serial_number}/powerSequences/{sequence_id}>"
            associated_device = f"<{base_url}{serial_number}>"
            
            # TODO: Catch exceptions from the SSA. Response and response code accordingly
            try:
                response_message, delay_status_code = bsh_delay_post(
                    power_sequence=power_sequence,
                    device_id=serial_number,
                    associated_device=associated_device,
                    sequence_id=sequence_id,
                    new_start_time=new_start_time
                )
            except Exception as e:
                delay_status_code = 500
                response_message = "Communication of cycle new start time failed. Try again later."
                logger.error(
                    f"SSA delayed start call failed with exception: {repr(e)}",
                    extra=cor_id
                )
        
        elif device_in_db.brand.lower() in ["whirlpool", "hotpoint"]:
            logger.info("Whirlpool Delay!\n", extra=cor_id)

            try:
                response_message, delay_status_code = wp_delay_post(
                    sequence_id=sequence_id,
                    device_address=serial_number,
                    new_start_time=new_start_time
                )
            except Exception as e:
                delay_status_code = 500
                response_message = "Communication of cycle new start time failed. Try again later."
                logger.error(
                    f"SSA delayed start call failed with exception: {repr(e)}",
                    extra=cor_id
                )
        
        else:
            msg = f"Delay request not implemented for brand: {device_in_db.brand}"
            logger.error(msg, extra=cor_id)
            response = Error(msg)
            
            return response, 400, cor_id


        delay_call_ok = False
        if delay_status_code != 200:
            logger.error(
                f"Delay to sequence {sequence_id} with new start time {new_start_time} FAILED!\n",
                extra=cor_id
            )
            
            response.append(DelaysStatus(
                sequence_id=sequence_id,
                serial_number=serial_number,
                message=response_message,
                delayed=False
            ))

        else:
            logger.info(
                f"Delayed sequence {sequence_id} to {new_start_time}... OK!\n",
                extra=cor_id
            )
            delay_call_ok = True
            response.append(DelaysStatus(
                sequence_id=sequence_id,
                serial_number=serial_number,
                message=response_message,
                delayed=True
            ))
        
        # Signal energy manager that recommendation was accepted
        if recommendation_id:
            rec_accept_response, rec_accept_code = post_flexibility_recommendations_accept(
                recommendation_id=recommendation_id,
                delay_call_ok=delay_call_ok,
                delay_call_description=response_message,
                cor_id=cor_id
            )
            if 400 <= rec_accept_code < 500:
                logger.error(
                    f"Failed to signal energy manager that recommendation "\
                    f"{recommendation_id} was accepted",
                    extra=cor_id
                )
                return rec_accept_response, rec_accept_code, cor_id

    logger.info(end_text, extra=cor_id)

    return response, 207, cor_id


def get_user_wp_appliances_get():
    connection_headers = connexion.request.headers
    cor_id = {"X-Correlation-ID": connection_headers["X-Correlation-ID"]}

    end_text = "Processed Get /get-user-wp-appliances request"


    # ------------------------------ Verify request permissions ------------------------------ #

    auth_response, auth_code = auth.verify_basic_authorization(connection_headers)

    # When Authorization is a required field
    if auth_code != 200 or auth_response is None:
        
        if auth_response is not None:
            logger.error(auth_response, extra=cor_id)
        else:
            logger.error("Request HAS to be made through the api gateway", extra=cor_id)
            auth_code = 401

        message = "Invalid credentials. Check logger for more info."
        response = Error(message)
        
        logErrorResponse(message, end_text, response, cor_id)
        return response, auth_code, cor_id

    else:
        user_id = auth_response


    operation_text = f"Get WP appliances for user {user_id}"
    logger.info(operation_text, extra=cor_id)

    logger.debug(f"User Id: {user_id}", extra=cor_id)


    # ----------------------------- Get user WP token from DB ----------------------------- #

    query_params = {
        "user-ids": [user_id]
    }
    headers = {
        "X-Correlation-ID": str(uuid.uuid4())
    }

    try:
        logger.info(f"Getting user's {user_id} profile from account manager.", extra=cor_id)
        user_profile_response = requests.get(
            Config.ACCOUNT_MANAGER_ENDPOINT + "/user", 
            params=query_params, 
            headers=headers
            )

        logger.info(f"Finished with status: {user_profile_response.status_code}", extra=cor_id)

        body = json.loads(user_profile_response.content.decode("utf-8"))
        logger.debug(f"User profile response body:\n{body}\n", extra=cor_id)
        body = body[0]  # Only one user
    
    except Exception as e:
        logger.error(repr(e), extra=cor_id)
        
        msg = f"Failed getting info from user {user_id} on account manager"
        logger.error(msg, extra=cor_id)
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return response, 400, cor_id
        

    if user_profile_response.status_code != 200:
        logger.error(f"Error on getting user profile:\n{json.dumps(body, indent=4)}\n", extra=cor_id)

        msg = "Failed to get user profile info"
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return response, user_profile_response.status_code, cor_id

    else:
        
        max_tries = 3
        current_try = 1

        while current_try <= max_tries:
            try:
                token = body["wp_token"]
                break
            except KeyError:
                logger.warning(
                    f"Try nr.{current_try}: WP token not found for user {user_id}\n" \
                    f"Has the user followed the WP authorization flow?\n", 
                    extra=cor_id
                    )

                sleep(1)
                current_try += 1

                if current_try > max_tries:
                    logger.error(
                        "Maximum tries for WP token exceeded. " \
                        "Looks like the user has not authenticated to his WP account properly.\n",
                        extra=cor_id
                        )

                    msg = "WP token not found. User unauthorized."
                    response = Error(msg)

                    logErrorResponse(msg, end_text, response, cor_id)
                    return response, 401, cor_id

    logger.info("WP token retrieved successfully", extra=cor_id)
    logger.debug(f"Token:\n{token}\n", extra=cor_id)


    # ------------------------------ Call ASK appliances SSA ------------------------------ #

    try:
        appliance_list, status_code = wp_appliances_ask(token=token)
        logger.info(f"Found {len(appliance_list)} appliances for user {user_id}\n", extra=cor_id)
    except Exception as e:
        logger.error(f"Error on ask appliances: {repr(e)}", extra=cor_id)
        status_code = 500

    if status_code != 200:
        return Error("WP ask appliances SSA failed!"), status_code, cor_id

    if len(appliance_list) == 0:
        # TODO: NOTIFICAÇÃO ao user de que ou a conta está errada, ou não tem nenhum dispositivo associado.
        logger.warning(
            f"User {user_id} has no devices associated with his Hotpoint user account. " \
            "Are the Hotpoint account credentials correct?\n\n" \
            f"User Hotpoint Token: {token}\n",
            extra=cor_id
        )
        return [], 200, cor_id

    # TODO: If device list is empty return 202. With message: user has no WP devices or they are already registered.
    # Usar o len(appliances_list) == 0 para saber se o user não tem devices ou se estes já estavam registados.

    for appliance in appliance_list:
        logger.info(f"Found appliance {appliance['deviceAddress']}", extra=cor_id)


    # ------------------------------ Call REGISTER appliances SSA ------------------------------ #

    for appliance in appliance_list:
        device_address = appliance["deviceAddress"]

        if appliance["registered"] == "false":
            try:
                response, status_code = wp_register_ask(
                    token=token, 
                    device_address=device_address,
                    register="true"
                    )
            except Exception as e:
                logger.error(f"Error on register appliance: {repr(e)}", extra=cor_id)
                status_code = 500
            
            if status_code != 200:
                return Error("WP register appliance SSA failed!"), status_code, cor_id
        
        else:
            logger.info(
                f"Appliance {device_address} of user {user_id} is already registered.\n",
                extra=cor_id
                )
            
            # TODO: Return error code for already registered device


    # --------------------------- Convert SSA result to API response --------------------------- #

    device_list = []
    for binding in appliance_list:

        device_brand = binding['brand']
        device_type = binding['type']
        serial_number = binding['deviceAddress']
        device_name = binding['name']


        # ------------------ Save to db ------------------ #

        # Check if appliance is a duplicated scan
        dup_app = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()

        if dup_app is not None:
        
            message = f"Machine from brand: {device_brand} and Serial Number: {serial_number}, already registered in the system!\n"
            logger.warning(message, extra=cor_id)
        
        else:

            shiftable_db_object = DBShiftableMachine(
                user_id=user_id,
                name=device_name,
                device_type=device_type,
                brand=device_brand,
                serial_number=serial_number,
                allow_hems=True,
                automatic_management=True,
                washing_cycles=[],
                not_disturb=[],
            )
            
            error_msg = f"Failed to save washing machine with serial number {serial_number} to db"
            response_code = add_row_to_table(db.session, shiftable_db_object, error_msg, cor_id)
            if response_code != 200:
                return Error(error_msg), response_code, cor_id

            logger.info(f"Washing machine with serial number {serial_number} saved to db.\n", extra=cor_id)

        # ------------------------------------------------ #


        nd = NotDisturb(
            sunday=[],
            monday=[],
            tuesday=[],
            wednesday=[],
            thursday=[],
            friday=[],
            saturday=[],
        ).to_dict()

        shiftable_machine = ShiftableMachine(
            name=device_name,
            device_type=device_type,
            brand=device_brand,
            serial_number=device_address,
            allow_hems=True,
            automatic_management=True,
            not_disturb=nd,
        )

        device_list.append(shiftable_machine)


        error_msg = f"Failed to save washing machine with serial number {serial_number} to db"
        response_code = commit_db_changes(db.session, error_msg, cor_id)
        if response_code != 200:
            return Error(error_msg), response_code, cor_id
        

    return device_list, 200, cor_id


def _ask_device_metadata(device_id, ssa, cor_id):
    try:
        device_metadata, status_code = bsh_appliances_metadata_ask(device_id, ssa)
        if status_code != 200:
            logger.error(f"Device metadata request failed with status code: {status_code}\n", extra=cor_id)
            device_type = "unknown"
            device_name = ""
        else:
            logger.info(device_metadata, extra=cor_id)

            if len(device_metadata) == 0:
                logger.error("Metadata not found", extra=cor_id)
                device_type = "unknown"
                device_name = ""
            
            else:
                device_type = device_metadata['deviceTypeName']
                device_name = device_metadata["deviceName"]
    
    except Exception as e:
        logger.error(f"Device metadata request failed with exception: {repr(e)}", extra=cor_id)
        device_type = "unknown"
        device_name = ""
        status_code = 500

    return status_code, device_type, device_name
    

def bsh_devices_get(device_brand, token, device_ids, ssa):
    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    
    # NOTE: Workaround for ETSI with TNO Spine adapter
    if os.environ.get("DEVICE_SSA", None) is not None:
        ssa = os.environ.get("DEVICE_SSA")

    end_text = "Processed GET /bsh-devices"
    logger.info("Processing /bsh-devices GET request", extra=cor_id)

    logger.debug(f"Device Brand: {device_brand}", extra=cor_id)
    logger.debug(f"User correlation token: {token}", extra=cor_id)
    logger.debug(f"Device ids retrieved from HC/Miele account: {device_ids}", extra=cor_id)
    logger.debug(f"Sender SSA KB asset ID: {ssa}", extra=cor_id)
    
    # Uniformization. BSH and Bosch are the same
    if device_brand == "bsh":
        device_brand = "bosch"


    # NOTE: We should pass the authorization to get the userID
    user_devices = DBShiftableMachine.query.filter_by(user_id=token).all()
    logger.debug(f"User devices in DB: {user_devices}", extra=cor_id)

    nd = NotDisturb(
        sunday=[],
        monday=[],
        tuesday=[],
        wednesday=[],
        thursday=[],
        friday=[],
        saturday=[],
    ).to_dict()

    new_devices = []
    for serial_number in device_ids:
        
        # Device exists in database but does not have correct metadata
        device_in_db = [device for device in user_devices if device.serial_number == serial_number]
        logger.debug(f"Devices in DB serial numbers: {device_in_db}", extra=cor_id)
        if len(device_in_db) != 0:
            logger.warning(f"Device {serial_number} already associated to user {token}", extra=cor_id)

            status_code, device_type, device_name = _ask_device_metadata(serial_number, ssa, cor_id)

            if status_code == 200:
                device = device_in_db[0]

                if device.device_type != device_type:
                    device.device_type = device_type
                    logger.debug(
                        f"Changed device type {device.device_type} to {device_type} " \
                        f"of device {serial_number}",
                        extra=cor_id
                    )
                
                new_device = ShiftableMachine(
                    name=device_name,
                    device_type=device_type,
                    brand=device_brand,
                    serial_number=serial_number,
                    device_ssa=ssa,
                    allow_hems=device.allow_hems,
                    not_disturb=nd
                )
                new_devices.append(new_device)
                
                
            response_code = 200
            continue

        
        # Device belongs to another user
        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
        if device_in_db is not None:
            msg = "Device already exists associated to another user"
            logger.error(msg, extra=cor_id)

            new_devices = Error(msg)
            response_code = 400
            
            break
        
        
        # New device asking for metadata
        status_code, device_type, device_name = _ask_device_metadata(serial_number, ssa, cor_id)
        
        # Build database object
        new_device_db = DBShiftableMachine(
            user_id=token,
            name=device_name,
            device_type=device_type,
            brand=device_brand,
            serial_number=serial_number,
            allow_hems=True,
            automatic_management=True,
            device_ssa=ssa,
        )
        
        logger.debug(f"New device: {new_device_db}", extra=cor_id)
        
        db_error_msg = f"Database failed to add device\n{new_device_db}\n"
        response_code = add_row_to_table(db.session, new_device_db, db_error_msg, cor_id)
        if response_code != 200:
            break

        
        # Build response object
        new_device = ShiftableMachine(
            name=device_name,
            device_type=device_type,
            brand=device_brand,
            serial_number=serial_number,
            allow_hems=True,
            automatic_management=True,
            device_ssa=ssa,
            not_disturb=nd
        )
        new_devices.append(new_device)
        
        
        ## Allow HEMS to control the devices by default
        if Config.SPINE_USE_RECIPIENT_SELECTOR:
            logger.info("Using recipient selector approach", extra=cor_id)
            
            message, _ = device_access_update_post(serial_number, ssa, True)
            logger.info(f"SSA device access update response: {message}", extra=cor_id)
    

        response_code = 201

        logger.info(f"Device {serial_number} added to user {token} devices", extra=cor_id)


    # Redirect to /device-failure in case it fails to add the devices
    if 400 <= response_code < 600:
        
        messages = json.dumps({
            "response_code": response_code,
        })
        session['messages'] = messages
        
        return redirect(f"{Config.BASE_PATH}/api/device/device-failure", code=302), 302, cor_id
    
    else:
        
        # Commit changes to database
        db_error_msg = f"Database failed to COMMIT to database\n"
        response_code = commit_db_changes(db.session, db_error_msg, cor_id)


        logger.info(f"{end_text}\n", extra=cor_id)
        
        messages = json.dumps({
            "response_code": response_code,
        })
        session['messages'] = messages

        return redirect(f"{Config.BASE_PATH}/api/device/device-success", code=302), 302, cor_id


@app.route("/api/device/device-success", methods=["GET"])
def device_success():
    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    logger.info("Processed GET /device-success", extra=cor_id)
    
    # messages = json.loads(session['messages'])
    logger.debug(session, extra=cor_id)

    return "", 200, cor_id


@app.route("/api/device/device-failure", methods=["GET"])
def device_failure():
    cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    logger.info("Processed GET /device-failure", extra=cor_id)
    
    messages = json.loads(session['messages'])
    logger.debug(messages, extra=cor_id)

    return "", messages['response_code'], cor_id


def ssa_device_allow_hems_post():
    connection_headers = connexion.request.headers
    cor_id = {"X-Correlation-ID": connection_headers["X-Correlation-ID"]}
    if connexion.request.is_json:
        allow_hems_request_body = AllowHemsRequestBody.from_dict(connexion.request.get_json())
    
    logger.info("Starting POST /ssa/device/allow-hems request", extra=cor_id)
    
    if Config.SPINE_USE_RECIPIENT_SELECTOR == False:
        logger.warning("Recipient selector is disabled. Ignoring request")
        msg = "Recipient selector is disabled"
        
        return Error(msg), 400, cor_id
    
    serial_number = allow_hems_request_body.serial_number
    device_ssa = allow_hems_request_body.device_ssa
    allow_hems = allow_hems_request_body.allow_hems
    

    end_text = "Processed POST /ssa/device/allow-hems request"


    # ------------------------------ Verify request permissions ------------------------------ #

    auth_response, auth_code = auth.verify_basic_authorization(connection_headers)

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
        
        device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()
        if device_in_db is None:
            logger.error(
                f"Device {serial_number} not found in database",
                extra=cor_id
                )
            
            msg = "Device not found!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 404, cor_id

        else:
            device_owner = device_in_db.user_id
        
        if device_owner != auth_response:
            logger.error(
                f"User {auth_response} trying to access different user devices ({device_owner})",
                extra=cor_id
                )
            
            msg = "Unauthorized action!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 403, cor_id
            

    else:
        logger.info(
            f"Only internal requests are allowed to make delays. Proceeding...",
            extra=cor_id
            )


    operation_text = f"Requesting access status update to {allow_hems} for device {serial_number}"
    logger.info(operation_text, extra=cor_id)
    
    
    # ------------------------------ SSA call ------------------------------ #
    
    message, status_code = device_access_update_post(serial_number, device_ssa, allow_hems)
    
    # message = f"Device {serial_number} access updated to {allow_hems}"
    # status_code = 200
    logger.info(f"SSA response: {message}", extra=cor_id)
    
    
    return message, status_code, cor_id
