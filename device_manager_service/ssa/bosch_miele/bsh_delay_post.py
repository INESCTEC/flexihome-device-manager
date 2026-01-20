from datetime import datetime

from device_manager_service import generalLogger, bsh_proactive_ssa
from device_manager_service.utils.ssa.process_bs import process_bsh_binding_set
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig


# Specific Service Adapter logic #

def bsh_delay_post(power_sequence, associated_device, device_id, sequence_id, new_start_time : datetime):
    generalLogger.info('Begin Bosch/Miele delay \"post\" service...')
    generalLogger.debug(f"To Sequence ID: {sequence_id}")
    generalLogger.debug(f"With new start time: {new_start_time}")

    # ---------------------- POST request ---------------------- #
    
    converted_datetime = new_start_time.strftime(format="%Y-%m-%dT%H:%M:%S.000Z")

    bindings = [{
        "powerSequence": power_sequence,
        "associatedDevice": associated_device,
        "deviceId": device_id,
        "sequenceID": sequence_id,
        "startTime": f'"{converted_datetime}"^^xsd:dateTime'
    }]

    generalLogger.info("# BOSCH/MIELE DELAYED START START POST #\n")

    react, react_response_code = bsh_proactive_ssa.ask_or_post(
        bindings=bindings,
        ki_id=bsh_proactive_ssa.bsh_delay_post_ki_id,
        response_wait_timeout_seconds=BSHConfig.BSH_DELAYED_START_RESPONSE_WAIT_TIMEOUT_SECONDS,
        self_heal=BSHConfig.BSH_DELAYED_START_SELF_HEAL_FLAG,
        delete_kb_when_self_heal=BSHConfig.BSH_DELAYED_START_DELETE_KB_FLAG,
        self_heal_tries=BSHConfig.BSH_DELAYED_START_SELF_HEAL_TRIES
    )


    if react_response_code == 200:

        if len(react["exchangeInfo"]) == 0:
            react_ack_response = "Delay failed"
            react_response_code = 500
            generalLogger.error("SSA communication could not reach Bosch server.")
        else:
            react_ack_response = process_bsh_binding_set(react["resultBindingSet"])

            # Handle error from spine adapter
            react_response_code = int(react_ack_response[0]["statusCodeValue"])
            if 400 <= react_response_code < 500:
                generalLogger.error(
                    f"POST request was unsuccessful with error code {react_response_code}.\n" \
                    f"Sending empty response...\n"
                    )
                react_ack_response = react_ack_response[0]["bodyText"]

            else:
                react_ack_response = "Delay successful"
        

    else:
        react_ack_response = "Delay failed"
        generalLogger.error(
            f"POST request was unsuccessful with error code {react_response_code}.\n" \
            f"Sending empty response...\n"
            )

    generalLogger.info('SSA POST delay completed. Exiting...')

    return react_ack_response, react_response_code
