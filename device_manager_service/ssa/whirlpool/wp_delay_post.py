from datetime import datetime, timedelta

from device_manager_service import generalLogger, whirlpool_proactive_ssa
from device_manager_service.utils.ssa.process_bs import process_whirlpool_binding_set
from device_manager_service.ssa.ssa_config.wp_config import WPConfig


# Specific Service Adapter logic #

def wp_delay_post(sequence_id, device_address, new_start_time : datetime):
    generalLogger.info('Begin WP POST delay SSA...')


    # ---------------------- ASK request ---------------------- #

    new_start_time = new_start_time - timedelta(hours=1)  # NOTE: WORKAROUND FOR TIMEZONE ISSUE
    
    converted_datetime = new_start_time.strftime(format="%Y-%m-%dT%H:%M:%SZ")
    generalLogger.debug(f"New start time: {converted_datetime}")

    bindings = [{
        "delay": "<https://www.example.org/delay>",
        "deviceAddress": f"\"{device_address}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "sequenceID": f"\"{sequence_id}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "playerid": f"\"{WPConfig.PLAYER_ID}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "startTime": f"\"{converted_datetime}\"^^<http://www.w3.org/2001/XMLSchema#dateTime>"
    }]

    generalLogger.info("# WP DELAYED START POST #\n")

    post_response, post_response_code = whirlpool_proactive_ssa.ask_or_post(
        bindings=bindings,
        ki_id=whirlpool_proactive_ssa.wp_delay_ki_id,
        response_wait_timeout_seconds=WPConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=WPConfig.ASK_POST_SELF_HEAL_TRIES
    )
    
    # cycle_in_db = DBShiftableCycle.query.filter_by(sequence_id=sequence_id).first()
        
    # if cycle_in_db is not None:
        
    #     duration = abs(cycle_in_db.expected_end_time - cycle_in_db.scheduled_start_time)
    #     expected_end_time = new_start_time + duration
    
    #     cycle_in_db.scheduled_start_time=new_start_time
    #     cycle_in_db.expected_end_time=expected_end_time

    #     cycle_in_db.is_optimized=True


    #     db_error_msg = f"Failed to commit changes to DB for cycle with sequence ID {sequence_id}.\n"
    #     commit_db_changes(db.session, db_error_msg)


    # ---------------------- Convert binding data to useful data for the service ---------------------- #

    if post_response_code == 200:
        
        # TODO: Check WP delay response for error message response field
        if len(post_response["exchangeInfo"]) == 0:
            post_ack_response = "Delay failed"
            post_response_code = 500
            generalLogger.error("SSA communication could not reach WP server.")
        else:
            post_ack_response = process_whirlpool_binding_set(post_response["resultBindingSet"])
            post_ack_response = "Delay Successful"
    
    else:
        post_ack_response = "Delay failed"
        generalLogger.error(
            f"POST request was unsuccessful with error code {post_response_code}.\n" \
            f"Sending empty response...\n"
        )

    generalLogger.info('SSA POST delay completed. Exiting...')

    return post_ack_response, post_response_code
