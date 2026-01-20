import time, requests, traceback
from time import sleep

from device_manager_service import generalLogger, db

from device_manager_service.ssa.bosch_miele.ssa_response_parsers.power_sequence import process_power_sequence
from device_manager_service.ssa.bosch_miele.ssa_response_parsers.connection_state import process_connection_state
from device_manager_service.utils.date.seconds_to_days_minutes_hours import seconds_to_days_minutes_hours

from device_manager_service.ssa.ssa_classes.bsh_ssa_react import BSHSSAReact
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig

from psycopg2 import OperationalError, DatabaseError


# Specific Service Adapter logic #

def bsh_pp_handle(exitEvent, bsh_ssa : BSHSSAReact):
    generalLogger.info('Begin Bosch power profile REACT thread SSA...')


    start = time.time()
    total_time = 0
    while not exitEvent.wait(timeout=0.01):
        session = db.create_scoped_session()
        
        current_time = time.time()
        if current_time - start >= 600:
            total_time += 600
            seconds_to_days_minutes_hours(total_time)
            start = current_time

        try:
            response, ki_id, handle_request_id, binding_set, requesting_kb_id = bsh_ssa.handle(
                kb_id=bsh_ssa.reactive_kb_id,
                self_heal=BSHConfig.BSH_POWER_PROFILE_SELF_HEAL_FLAG,
                refresh_kb=BSHConfig.BSH_TIME_INTERVAL_TO_REFRESH_KB_MINUTES,
                debug=BSHConfig.HANDLE_DEBUG_FLAG
            )

            if response.status_code < 300:
                if ki_id is not None:
                    generalLogger.info(f"Handle Request ID: {handle_request_id}")
                    generalLogger.info(f"Requesting KB ID: {requesting_kb_id}")
                    generalLogger.info(f"KI ID of requesting interaction: {ki_id}")

                if ki_id == bsh_ssa.bsh_pp_react_ki_id:
                    response, status_code = bsh_ssa.answer_or_react(
                        request_id=handle_request_id,
                        bindings=[],
                        ki_id=ki_id,
                        response_wait_timeout_seconds=BSHConfig.REACTIVE_WAIT_TIMEOUT_SECONDS,
                        self_heal=BSHConfig.REACTIVE_SELF_HEAL_FLAG,
                        delete_kb_when_self_heal=BSHConfig.REACTIVE_DELETE_KB_FLAG,
                        self_heal_tries=BSHConfig.REACTIVE_SELF_HEAL_TRIES
                    )
                    process_power_sequence(session, binding_set)
                elif ki_id == bsh_ssa.connection_state_react_ki_id:
                    response, status_code = bsh_ssa.answer_or_react(
                        request_id=handle_request_id,
                        bindings=[],
                        ki_id=ki_id,
                        response_wait_timeout_seconds=BSHConfig.REACTIVE_WAIT_TIMEOUT_SECONDS,
                        self_heal=BSHConfig.REACTIVE_SELF_HEAL_FLAG,
                        delete_kb_when_self_heal=BSHConfig.REACTIVE_DELETE_KB_FLAG,
                        self_heal_tries=BSHConfig.REACTIVE_SELF_HEAL_TRIES
                    )
                    process_connection_state(session, binding_set)
                else:
                    if ki_id is not None:
                        generalLogger.warning(f"Unexpected KI ID received: {ki_id}")
                        generalLogger.warning(f"From KB: {requesting_kb_id}\n")
            else:
                generalLogger.warning(f"Handle request status code: {response.status_code}")
                generalLogger.warning(f"Handle request response: {response.content}")
        except (OperationalError, DatabaseError) as e:
            generalLogger.error("Database error catched!")
            generalLogger.error(repr(e))
            traceback.print_exc()
            
            session.rollback()
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))
            
            generalLogger.info(
                f"Handle failed. Restarting long polling in {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds"
            )
            sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)
            
            try:
                bsh_ssa.run_setup(delete_kb=True)
            
            except requests.HTTPError as e:
                traceback.print_exc()
                generalLogger.error("Expected exception: HTTP Error")
                generalLogger.error(repr(e))
            
            except Exception as e:
                traceback.print_exc()
                generalLogger.error("Unexpected exception!")
                generalLogger.error(repr(e))

        session.close()

    generalLogger.info('SSA thread stopped. Exiting...')
