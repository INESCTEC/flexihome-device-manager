import psycopg2
from datetime import datetime, timedelta, timezone
from dateutil import parser, tz
from sqlalchemy import desc

from device_manager_service import db, generalLogger
from device_manager_service.utils.ssa.process_bs import process_bsh_binding_set
from device_manager_service.models.db_models import (
    DBShiftableMachine,
    DBShiftableCycle,
    DBShiftablePowerProfile
)
from device_manager_service.utils.database.db_interactions import (
    add_row_to_table,
    commit_db_changes,
    delete_and_commit
)
from device_manager_service.clients.hems_services.energy_manager import delete_recommendation


def process_power_sequence(session, binding_set):
    processed_binding_set = process_bsh_binding_set(binding_set)
            
    if len(processed_binding_set) != 0:
        # Process common part of the power profile bindings
        common_cycle_data = processed_binding_set[0]
        common_cycle_data["deviceId"] = common_cycle_data["deviceId"].replace(">", "").split("/")[-1]

        # Device exists?
        device_in_db = session.query(DBShiftableMachine).filter_by(serial_number=common_cycle_data['deviceId']).first()
        # session.expunge_all()
        
        if device_in_db is not None:
            generalLogger.info(f"Sequence {common_cycle_data['sequenceID']} for device {common_cycle_data['deviceId']}")
            
            if device_in_db.brand.lower() == "bosch":
                if common_cycle_data['state'] == "scheduled":
                    save_power_sequence(session, common_cycle_data, processed_binding_set, device_in_db)
                elif common_cycle_data['state'] == "inactive":
                    delete_device_current_cycle(session, device_in_db, delete_from_cycle_table=True)
                elif common_cycle_data['state'] == "running":
                    save_power_sequence(
                        session, common_cycle_data, processed_binding_set, device_in_db,
                        check_existing_cycle=True
                    )
                elif common_cycle_data['state'] == "paused":
                    generalLogger.info(
                        f"Device {device_in_db.serial_number} state changed to " \
                        f"{common_cycle_data['state']}\nNothing to do...."
                    )
                elif common_cycle_data['state'] == "completed":
                    delete_device_current_cycle(session, device_in_db, delete_from_cycle_table=False)
                else:
                    generalLogger.error(f"State '{common_cycle_data['state']}' is unknown")
            

            elif device_in_db.brand.lower() == "miele":
                # Device has nothing scheduled
                if (common_cycle_data['state'] == "inactive") and (device_in_db.current_cycle_id is None):
                    generalLogger.debug(f"Device {device_in_db.serial_number} has nothing scheduled")
                
                elif (common_cycle_data['state'] == "inactive") and (device_in_db.current_cycle_id is not None):
                    common_cycle_data = convert_str_to_timestamps(common_cycle_data)
                    
                    cycle_in_db = session.query(DBShiftableCycle).filter_by(
                        id=device_in_db.current_cycle_id,
                        shiftable_machine_id=device_in_db.id
                    ).first()
                    # Cycle end time is in UTC, because it is saved in the DB as UTC
                    cycle_end_time = cycle_in_db.expected_end_time.replace(tzinfo=tz.gettz("UTC"))
                    up_margin = (datetime.now(timezone.utc) + timedelta(minutes=1)).replace(tzinfo=tz.gettz("UTC"))
                    down_margin = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(tzinfo=tz.gettz("UTC"))
                    
                    # Program finishes normally
                    if up_margin >= cycle_end_time >= down_margin:
                        generalLogger.debug(
                            f"Program finished normally. " \
                            f"Deleting current cycle {device_in_db.current_cycle_id}"
                        )
                        # Delete current cycle
                        delete_device_current_cycle(session, device_in_db, delete_from_cycle_table=False)
                    
                    # Program is cancelled
                    else:
                        # Delete current cycle from machine and from cycle table
                        generalLogger.debug(
                            f"Program was cancelled. " \
                            f"Deleting cycle {device_in_db.current_cycle_id}"
                        )
                        delete_device_current_cycle(session, device_in_db, delete_from_cycle_table=True)
                
                # New cycle scheduled
                elif (common_cycle_data['state'] == "scheduled") and (device_in_db.current_cycle_id is None):
                    # Increment sequence id
                    sequence_id = increment_sequence_id(session, device_in_db)
                    common_cycle_data['sequenceID'] = sequence_id
                    
                    generalLogger.debug(f"Device {device_in_db.serial_number} has new cycle scheduled: {sequence_id}")
                        
                    save_power_sequence(session, common_cycle_data, processed_binding_set, device_in_db)
                
                # Device has a cycle scheduled, but already saved
                elif (common_cycle_data['state'] == "scheduled") and (device_in_db.current_cycle_id is not None):
                    generalLogger.info(
                        f"Device {device_in_db.serial_number} has scheduled cycle " \
                        f"{common_cycle_data['sequenceID']}"
                    )
                
                # User running program manually without delayed start
                elif (common_cycle_data['state'] == "running") and (device_in_db.current_cycle_id is None):
                    # Increment sequence id
                    sequence_id = increment_sequence_id(session, device_in_db)
                    common_cycle_data['sequenceID'] = sequence_id
                    
                    generalLogger.debug(
                        f"Device {device_in_db.serial_number} " \
                        f"has been mannually scheduled. New sequence ID: {sequence_id}"
                    )
                        
                    save_power_sequence(session, common_cycle_data, processed_binding_set, device_in_db)
                
                # Others states that are not contemplated in this logic (pause, etc.)
                else:
                    
                    if common_cycle_data['state'] not in ["running", "scheduled", "inactive"]:
                        generalLogger.error(
                            f"Device {device_in_db.serial_number} has unexpected state: " \
                            f"{common_cycle_data['state']}\n"
                        )
                        
                    else:
                        generalLogger.debug(f"Device {device_in_db.serial_number} is in state {common_cycle_data['state']}\n")
            else:
                generalLogger.error(f"Device brand '{device_in_db.brand.lower()}' is unkown...")
        else:
            generalLogger.error(f"Device {common_cycle_data['deviceId']} does not exists in DB!\n")
    else:
        generalLogger.error(f"Power Profile is empty.\nNot saving object to db...\n")



def convert_str_to_timestamps(cycle_bindings):    
    cycle_bindings["startTime"] = parser.parse(cycle_bindings["startTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["earliestStartTime"] = parser.parse(cycle_bindings["earliestStartTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["latestEndTime"] = parser.parse(cycle_bindings["latestEndTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["endTime"] = parser.parse(cycle_bindings["endTime"], tzinfos={"Z": tz.gettz("UTC")})


    return cycle_bindings


def increment_sequence_id(session, device):
    # Get existing cycle with biggest sequence id
    existing_cycle = session.query(DBShiftableCycle).filter_by(
        shiftable_machine_id=device.id
    ).order_by(
        desc(DBShiftableCycle.sequence_id)
    ).first()
    
    # Increment sequence id
    if existing_cycle is not None:
        incremented_sequence_id = str(int(existing_cycle.sequence_id) + 1)
    else:
        incremented_sequence_id = "1"
    
    
    return incremented_sequence_id


def save_power_sequence(session, cycle_bindings, power_profile_bindings, device, check_existing_cycle=False):
    generalLogger.info(f"Saving cycle {cycle_bindings['sequenceID']} in database...")
    
    
    # PARSE DATES FROM BINDING SETS #
    cycle_bindings = convert_str_to_timestamps(cycle_bindings)
    
    
    # CHECK IF POWER SEQUENCE EXISTS #
    if check_existing_cycle:
        existing_cycle = session.query(DBShiftableCycle).filter_by(
            sequence_id=cycle_bindings['sequenceID'],
            shiftable_machine_id=device.id
        ).first()
        # Do not save in case there is already a cycle with same ID in the DB
        if existing_cycle is not None:
            generalLogger.warning(
                f"Device {device.serial_number} already has cycle {cycle_bindings['sequenceID']} in DB"
            )
            return
    

    # SAVE POWER PROFILE ASSOCIATED WITH DEVICE #
    
    power_profile = []
    for pp in power_profile_bindings:
        
        # Transform default duration from 01:03:00 to 63 minutes
        duration_time = datetime.strptime(pp["defaultDuration_1"], "%H:%M:%S").time()
        duration_minutes = duration_time.hour * 60 + duration_time.minute

        slot_profile = DBShiftablePowerProfile(
            slot=pp["slotNumber_1"],
            max_power=pp["valueMax_1"],
            min_power=pp["valueMin_1"],
            expected_power=pp["valueExpectedValue_1"],
            power_units="W",
            duration=duration_minutes,
            duration_units="minutes",
        )
        
        error_msg = f"Failed to flush slot:\n{slot_profile}"
        response_code = add_row_to_table(session, slot_profile, error_msg)
        if response_code != 200:
            raise psycopg2.DatabaseError(error_msg)

        power_profile.append(slot_profile)

        generalLogger.debug(f"Flushed slot {pp['slotNumber_1']}...")

    # Describe machine cycle
    machine_cycle = DBShiftableCycle(
        sequence_id=cycle_bindings['sequenceID'],
        earliest_start_time=cycle_bindings["earliestStartTime"],
        latest_end_time=cycle_bindings["latestEndTime"],
        scheduled_start_time=cycle_bindings["startTime"],
        expected_end_time=cycle_bindings["endTime"],
        program="",
        is_optimized=False,
        power_profile=power_profile,
        shiftable_machine_id=device.id,
    )

    error_msg = f"Failed to save cycle {cycle_bindings['sequenceID']} in database"
    response_code = add_row_to_table(session, machine_cycle, error_msg)
    if response_code != 200:
        raise psycopg2.DatabaseError(error_msg)
    
    # Update current cycle
    device.current_cycle_id = machine_cycle.id
    
    response_code = commit_db_changes(session, error_msg)
    if response_code != 200:
        raise psycopg2.DatabaseError(error_msg)
    
    return


def delete_device_current_cycle(session, device, delete_from_cycle_table=True):
    # Get device serial number before the database session is closed
    device_serial_number = device.serial_number
    if device.current_cycle_id is None:
        generalLogger.warning(f"Device {device_serial_number} does not have a scheduled cycle")
        return
        
    device_current_cycle = session.query(DBShiftableCycle).filter_by(id=device.current_cycle_id).first()
    generalLogger.debug(device_current_cycle)
    
    if device_current_cycle is None:
        generalLogger.error(
            f"There is no cycle with id {device.current_cycle_id}...\n" \
            f"Removing the current cycle from device {device_serial_number}"
        )
        
        device_current_cycle.current_cycle_id = None
        
        error_msg = f"Failed to change current cycle of device {device_serial_number}"
        response_code = commit_db_changes(session, error_msg)
        
        if response_code != 200:
            raise psycopg2.DatabaseError(error_msg)
        
        return
    
    
    if delete_from_cycle_table:
        error_msg = f"Failed to delete cycle with id: {device.current_cycle_id} " \
            f"from device {device_serial_number}\n"
        response_code = delete_and_commit(session, device_current_cycle, error_msg)
        
        if response_code != 200:
            raise psycopg2.DatabaseError("Failed to delete cycle")
        
        # Delete flex recommendation associated with cycle 
        del_response, del_status_code = delete_recommendation(
            device_serial_number, device_current_cycle.sequence_id
        )
        if 400 <= del_status_code < 500:
            generalLogger.warning(
                f"Failed to delete recommendation from Energy Manager Service: {del_response['error']}"
            )
    
    return
