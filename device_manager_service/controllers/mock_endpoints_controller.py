import connexion, json, uuid
from datetime import datetime, timedelta
from time import sleep
from random import randint

from device_manager_service import auth, logger, db

from device_manager_service.models import (
    AddDeviceRequestBody,
    ScheduleCycleRequestBody,
    Error,
    ShiftableMachine,
    MachineCycle,
    PowerProfile,
    NotDisturb
)

from device_manager_service.models.db_models import (
    DBShiftableMachine,
    DBShiftableCycle,
    DBShiftablePowerProfile,
    DBEvent
)

from device_manager_service.models.events import CycleSchema, CycleScheduledEventType

from device_manager_service.utils.random_generation import generate_random_sequence_id
from device_manager_service.utils.logs import logErrorResponse
from device_manager_service.utils.database.db_interactions import add_and_commit, add_row_to_table


class DTEncoder(json.JSONEncoder):
    def default(self, obj):
        # 👇️ if passed in object is datetime object
        # convert it to a string
        if isinstance(obj, datetime):
            return str(obj)
        # 👇️ otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)



def device_post(brand):
    if connexion.request.is_json:
        add_device_request_body = AddDeviceRequestBody.from_dict(
            connexion.request.get_json()
        )
    serial_number = add_device_request_body.serial_number

    connection_headers = connexion.request.headers
    cor_id = {"X-Correlation-ID": connection_headers["X-Correlation-ID"]}

    end_text = "Processed POST /device request"
    # operation_text = "add device to his account"
    logger.info(
        f"Brand: {brand}\nBody: {add_device_request_body.__repr__()}",
        extra=cor_id
    )

    auth_response, auth_response_code = auth.verify_basic_authorization(
        connection_headers
    )

    if auth_response_code != 200:
        error_message = Error(auth_response)
        logErrorResponse(auth_response, end_text, error_message, cor_id)
        return error_message, auth_response_code, cor_id

    else:
        user_id = auth_response


    dup_app = DBShiftableMachine.query.filter_by(
        serial_number=serial_number, brand=brand
    ).first()
    if dup_app is not None:
        message = f"Machine from brand: {brand} " \
        f"and Serial Number: {serial_number}, already registered in the system."

        logger.error(message, extra=cor_id)
        response = Error(message)

        return response, 400, cor_id


    sleep(2)  # simulação de situação real.

    device_type = "WashingMachine"

    # guardar na BD
    shiftable_db_object = DBShiftableMachine(
        user_id=user_id,
        name="mock name",
        device_type=device_type,
        brand=brand,
        serial_number=serial_number,
        automatic_management=True,
        washing_cycles=[],
        not_disturb=[],
    )

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
        name="mock name",
        device_type=device_type,
        brand=brand,
        serial_number=serial_number,
        allow_hems=True,
        automatic_management=True,
        not_disturb=nd,
    )

    logger.info(f"Saving object to DB: {shiftable_db_object}\n", extra=cor_id)
    
    error_msg = f"Error saving mock device to DB: {serial_number}"
    response_code = add_and_commit(db.session, shiftable_db_object, error_msg, cor_id)
    if response_code != 200:
        return Error(error_msg), response_code, cor_id
    

    logger.info(f"Object Saved. Request ended with status: {200}", extra=cor_id)

    return shiftable_machine, 200, cor_id


def schedule_cycle_by_device_post(serial_number):  # noqa: E501
    """Schedule new cycle for appliance (MOCK manufacturer SSA endpoint).

     # noqa: E501

    :param x_correlation_id:
    :type x_correlation_id:
    :param serial_number:
    :type serial_number: str
    :param schedule_cycle_request_body:
    :type schedule_cycle_request_body: dict | bytes
    :param authorization:
    :type authorization: str

    :rtype: MachineCycle
    """
    if connexion.request.is_json:
        schedule_cycle_request_body = ScheduleCycleRequestBody.from_dict(
            connexion.request.get_json()
        )  # noqa: E501

    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}

    end_text = "Processed POST /schedule-cycle-by-device request"
    operation_text = f"schedule new cycle for device {serial_number}"
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



    logger.info(
        "Mimicking SSA REACT response for new cycle created by the user....",
        extra=cor_id,
    )


    # ------------------ Check if Device exists in user database ------------------ #

    device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()

    if device_in_db is None:

        logger.error(f"No device with ID '{serial_number}' in Database...", extra=cor_id)
        msg = "One or more device IDs not associated with the user."
        response = Error(msg)

        logErrorResponse(msg, end_text, response, cor_id)
        return response, 400, cor_id


    # ------------------ Fake user input from the manufacturer app ------------------ #

    scheduled_start_time = schedule_cycle_request_body.scheduled_start_time
    program = schedule_cycle_request_body.program

    # -------------- Check if cycle already exists in DB for that specific machine -------------- #

    existing_cycle = DBShiftableCycle.query.filter(
        scheduled_start_time >= DBShiftableCycle.scheduled_start_time,
        scheduled_start_time <= DBShiftableCycle.expected_end_time,
        DBShiftableCycle.shiftable_machine_id == device_in_db.id,
    ).first()

    if existing_cycle is not None:
        message = f"There is an already scheduled cycle for the machine {device_in_db.serial_number} " \
            f"starting at {existing_cycle.scheduled_start_time} " \
            f"and ending at {existing_cycle.expected_end_time}"

        logger.error(message, extra=cor_id)
        return Error(message), 400, cor_id


    # -------------- Fake Machine cycle return from SSA -------------- #

    response = []
    sequence_id = generate_random_sequence_id()
    now = datetime.now() + timedelta(days=1)  # scheduling for day ahead

    earliest_start_time = datetime(now.year, now.month, now.day, 6, 0, 0)
    latest_end_time = datetime(now.year, now.month, now.day, 23, 0, 0)
    expected_end_time = scheduled_start_time + timedelta(minutes=90)  # Average program takes 1h30m
    is_optimized = True

    power_profile = []
    power_profile_db = []
    for i in range(4):  # Fake 4 different slots for power profile of program

        if device_in_db.brand == "Whirlpool":
            max_power = randint(100, 3000)
            min_power = None
            expected_power = None

        else:
            max_power = randint(100, 3000)
            min_power = randint(int(max_power * 0.1), int(max_power * 0.5))
            expected_power = randint(min_power, max_power)

        # Return object
        slot_profile = PowerProfile(
            slot=i + 1,
            max_power=max_power,
            min_power=min_power,
            expected_power=expected_power,
            power_units="W",
            duration=randint(4, 60),
            duration_units="minutes",
        )
        power_profile.append(slot_profile)

        # Save to DB
        slot_profile_db = DBShiftablePowerProfile(
            slot=slot_profile.slot,
            max_power=slot_profile.max_power,
            min_power=slot_profile.min_power,
            expected_power=slot_profile.expected_power,
            power_units=slot_profile.power_units,
            duration=slot_profile.duration,
            duration_units=slot_profile.duration_units,
        )

        error_msg = "Failed to save power profile to DB."
        response_code = add_row_to_table(db.session, slot_profile_db, error_msg, cor_id)
        if response_code != 200:
            return Error(error_msg), response_code, cor_id
        
        power_profile_db.append(slot_profile_db)

    # Return object
    machine_cycle = MachineCycle(
        sequence_id=sequence_id,
        earliest_start_time=earliest_start_time,
        latest_end_time=latest_end_time,
        scheduled_start_time=scheduled_start_time,
        expected_end_time=expected_end_time,
        program=program,
        is_optimized=is_optimized,
        power_profile=power_profile,
    )

    # Save new cycle to DB
    machine_cycle_db = DBShiftableCycle(
        sequence_id=sequence_id,
        earliest_start_time=earliest_start_time,
        latest_end_time=latest_end_time,
        scheduled_start_time=scheduled_start_time,
        expected_end_time=expected_end_time,
        program=program,
        is_optimized=is_optimized,
        power_profile=power_profile_db,
        shiftable_machine_id=device_in_db.id,
    )
    
    logger.info(
        f"New machine scheduled cycle: {machine_cycle_db}\n",
        extra=cor_id
    )

    error_msg = "Failed to save new cycle to DB."
    response_code = add_row_to_table(db.session, machine_cycle_db, error_msg, cor_id)
    if response_code != 200:
        return Error(error_msg), response_code, cor_id


    # Cycles scheduled received event
    cycle_schema = CycleSchema()
    payload = cycle_schema.dump(cycle_schema)

    logger.info(f"Cycle schema payload:\n{payload}", extra=cor_id)

    event = DBEvent(
        aggregateid=uuid.uuid4(), type=CycleScheduledEventType, payload=payload
    )

    error_msg = "Failed to save event to DB."
    response_code = add_and_commit(db.session, event, error_msg, cor_id)
    if response_code != 200:
        return Error(error_msg), response_code, cor_id

    logger.info("END POST /schedule-cycle REQUEST...", extra=cor_id)

    response = machine_cycle

    return response, 200, cor_id
