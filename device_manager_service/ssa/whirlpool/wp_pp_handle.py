import json
import time
import psycopg2
import requests
import traceback
from datetime import datetime
from dateutil import parser, tz
from time import sleep

from device_manager_service import generalLogger, db

from device_manager_service.models.db_models import (
    DBShiftablePowerProfile,
    DBShiftableCycle,
    DBShiftableMachine
)

from device_manager_service.utils.ssa.process_bs import process_whirlpool_binding_set
from device_manager_service.utils.date.seconds_to_days_minutes_hours import seconds_to_days_minutes_hours
from device_manager_service.utils.database.db_interactions import add_row_to_table, add_and_commit, commit_db_changes, delete_and_commit

from device_manager_service.clients.hems_services.energy_manager import delete_recommendation

from device_manager_service.ssa.ssa_classes.whirlpool_ssa_react import WhirlpoolSSAReact
from device_manager_service.ssa.ssa_config.wp_config import WPConfig

from psycopg2 import OperationalError, DatabaseError

WHIRLPOOL_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _convert_str_to_timestamps(cycle_bindings):
    cycle_bindings["startTime"] = parser.parse(
        cycle_bindings["startTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["earliestStartTime"] = parser.parse(
        cycle_bindings["earliestStartTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["latestEndTime"] = parser.parse(
        cycle_bindings["latestEndTime"], tzinfos={"Z": tz.gettz("UTC")})
    cycle_bindings["endTime"] = parser.parse(
        cycle_bindings["endTime"], tzinfos={"Z": tz.gettz("UTC")})

    return cycle_bindings


def _save_power_profile(session, cycle_bindings, power_profile_bindings, device):
    generalLogger.info(
        f"Saving cycle {cycle_bindings['sequenceID']} in database...\n")

    # Save to database in UTC format #

    cycle_bindings = _convert_str_to_timestamps(cycle_bindings)

    # TODO: Se o ciclo for apenas modificado (o utilizador muda a hora de inicio)

    cycle_in_db = session.query(DBShiftableCycle).filter_by(
        sequence_id=cycle_bindings['sequenceID']).first()

    # ---------------------- Save Power Profile in database ---------------------- #

    if cycle_in_db is None:
        power_profile = []
        for pp in power_profile_bindings:

            # Transform default duration from 01:03:00 to 63 minutes
            duration_time = datetime.strptime(
                pp["defaultDuration"], "%H:%M:%S").time()
            duration_minutes = duration_time.hour * 60 + duration_time.minute

            slot_profile = DBShiftablePowerProfile(
                slot=pp["slotNumber"],
                max_power=pp["valueMax"],
                min_power=None,
                expected_power=None,
                power_units="W",
                duration=duration_minutes,
                duration_units="minutes",
            )

            error_msg = f"Failed to flush slot:\n{slot_profile}"
            response_code = add_row_to_table(session, slot_profile, error_msg)
            if response_code != 200:
                raise psycopg2.DatabaseError(error_msg)

            power_profile.append(slot_profile)

            generalLogger.debug(f"Flushed slot {pp['slotNumber']}...")

        # Describe machine cycle
        machine_cycle = DBShiftableCycle(
            sequence_id=cycle_bindings['sequenceID'],
            earliest_start_time=cycle_bindings["earliestStartTime"],
            latest_end_time=cycle_bindings["latestEndTime"],
            scheduled_start_time=cycle_bindings["startTime"],
            expected_end_time=cycle_bindings["endTime"],
            program=cycle_bindings["taskID"],
            is_optimized=False,
            power_profile=power_profile,
            shiftable_machine_id=device.id,
        )

        error_msg = f"Failed to save cycle {cycle_bindings['sequenceID']} in database"
        response_code = add_and_commit(session, machine_cycle, error_msg)
        if response_code != 200:
            raise psycopg2.DatabaseError(error_msg)

    else:
        cycle_in_db.earliest_start_time = cycle_bindings["earliestStartTime"]
        cycle_in_db.latest_end_time = cycle_bindings["latestEndTime"]
        cycle_in_db.scheduled_start_time = cycle_bindings["startTime"]
        cycle_in_db.expected_end_time = cycle_bindings["endTime"]

        error_msg = f"Failed to update cycle {cycle_bindings['sequenceID']} in database"
        response_code = commit_db_changes(session, error_msg)
        if response_code != 200:
            raise psycopg2.DatabaseError(error_msg)

    generalLogger.info(
        f"Cycle {cycle_bindings['sequenceID']} saved in database!\n")

    return


def _delete_power_sequence(session, device_serial_number, sequence_id):
    cycle = session.query(DBShiftableCycle).filter_by(
        sequence_id=sequence_id).first()
    generalLogger.debug(cycle)

    if cycle is None:
        generalLogger.error(
            f"There is no cycle with sequence id {sequence_id}...\n"
            f"NO cycle removed."
        )

    else:

        error_msg = f"Failed to delete cycle with id: {sequence_id} " \
            f"from device {device_serial_number}"
        response_code = delete_and_commit(session, cycle, error_msg)
        if response_code != 200:
            raise psycopg2.DatabaseError(error_msg)

        # Delete flex recommendation associated with cycle
        del_response, del_status_code = delete_recommendation(
            device_serial_number, sequence_id
        )
        if 400 <= del_status_code < 500:
            generalLogger.warning(
                f"Failed to delete recommendation from Energy Manager Service: {del_response['error']}"
            )

    return


def bindings_to_json(bindings):

    # When Multiple Installation_codes are used in a single request, start_date and end_date must be the same for every installation_code
    parsed_parameters = {
        'powerSequence': bindings[0]['powerSequence'],
        'sequenceID': bindings[0]['sequenceID'],
        'deviceAddress': bindings[0]['deviceAddress']
    }

    return parsed_parameters


# Specific Service Adapter logic (Power Profile) #

def wp_power_profile_handle(exitEvent, whirlpool_ssa: WhirlpoolSSAReact):
    generalLogger.info('Begin WP Power Profile thread SSA...')

    # ---------------------- Handle Power Profile requests ---------------------- #

    start = time.time()
    total_time = 0
    while not exitEvent.wait(timeout=0.01):
        current_time = time.time()
        if current_time - start >= 600:
            total_time += 600
            seconds_to_days_minutes_hours(total_time)
            start = current_time

        try:
            response, ki_id, handle_request_id, binding_set, requesting_kb_id = whirlpool_ssa.handle(
                kb_id=whirlpool_ssa.reactive_kb_id,
                self_heal=True,
                refresh_kb=WPConfig.WP_TIME_INTERVAL_TO_REFRESH_KB_MINUTES,  # Refresh KB every hour
                debug=WPConfig.HANDLE_DEBUG_FLAG
            )

        except Exception as e:
            generalLogger.error(repr(e))

            generalLogger.info(
                f"Handle failed. Restarting long polling in {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds"
            )
            sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)

            try:
                whirlpool_ssa.run_setup(delete_kb=True)

            except requests.HTTPError as e:
                traceback.print_exc()
                generalLogger.error("Expected exception: HTTP Error")
                generalLogger.error(repr(e))

            except Exception as e:
                traceback.print_exc()
                generalLogger.error("Unexpected exception!")
                generalLogger.error(repr(e))

            continue

        if response.status_code == 200:

            generalLogger.debug(
                f"Handle request status code: {response.status_code}")
            generalLogger.debug(f"KI ID of requesting interaction: {ki_id}")
            generalLogger.info(f"Handle Request ID: {handle_request_id}")
            generalLogger.info(f"Requesting KB ID: {requesting_kb_id}")

            # In case we receive a binding set from an unexpected KI
            if ki_id != whirlpool_ssa.wp_react_pp_ki_id:
                generalLogger.warning(
                    f"Unexpected binding set received from KI: {ki_id}")
                generalLogger.warning(f"From KB: {requesting_kb_id}\n")
                continue

            generalLogger.info(f"Received \"post\" from KB {requesting_kb_id}")
            generalLogger.info(f"{json.dumps(binding_set, indent=4)}\n")

            # REACT
            react_body = bindings_to_json(binding_set)
            bindings = [react_body]
            whirlpool_ssa.answer_or_react(
                request_id=handle_request_id,
                bindings=bindings,
                ki_id=ki_id
            )

            # ---------------------- Process the received power profile ---------------------- #

            processed_binding_set = process_whirlpool_binding_set(binding_set)

            if len(processed_binding_set) == 0:
                generalLogger.error(
                    f"Power Profile is empty.\nNot saving object to db...\n"
                )
                continue

            # Since bindings are flat, there is data that is the same for the entire binding set #

            common_cycle_data = processed_binding_set[0]

            # Check if the device, which the cycle belongs to, exists in the database #
            session = db.create_scoped_session()
            try:
                device_in_db = session.query(DBShiftableMachine).filter_by(
                    serial_number=common_cycle_data['deviceAddress']
                ).first()
                if device_in_db is None:
                    generalLogger.error(
                        f"No device with serial number "
                        f"'{common_cycle_data['deviceAddress']}' in Database..."
                    )
                    continue
                generalLogger.debug(
                    f"Device {common_cycle_data['deviceAddress']} found in database.\n")

                if common_cycle_data['state'] == "scheduled" and common_cycle_data['taskID'].lower() != "null":
                    _save_power_profile(
                        session, common_cycle_data, processed_binding_set, device_in_db)
                elif common_cycle_data['state'] == "scheduled" and common_cycle_data['taskID'].lower() == "null":
                    _delete_power_sequence(
                        session, device_in_db.serial_number, common_cycle_data["sequenceID"])
                else:
                    generalLogger.warning(
                        f"State {common_cycle_data['state']} unknown and "
                        f"task ID {common_cycle_data['taskID']}"
                    )
            except (OperationalError, DatabaseError) as e:
                generalLogger.error("Database error catched!")
                generalLogger.error(repr(e))
                traceback.print_exc()

                session.rollback()
            except Exception as e:
                traceback.print_exc()
                generalLogger.error(repr(e))

            session.close()
        else:
            generalLogger.warning(
                f"Handle request status code: {response.status_code}")
            generalLogger.warning(
                f"Handle request response: {response.content}")

    generalLogger.info('SSA received event. Exiting...')
