from device_manager_service import generalLogger, bsh_proactive_ssa

from device_manager_service.utils.ssa.process_bs import process_bsh_binding_set
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig


# Specific Service Adapter logic #

def bsh_appliances_metadata_ask(device_id, ssa):
    generalLogger.info('Begin BOSCH/MIELE ASK appliances metadata SSA...')

    # ---------------------- ASK request ---------------------- #

    # deviceId -> {ssa}/devices/{device_id}
    
    bindings = [{
        "device": f"<{ssa}/devices/{device_id}>",
    }]


    generalLogger.info(f"# BOSCH/MIELE APPLIANCES METADATA ASK #\n")

    ask_response, ask_response_code = bsh_proactive_ssa.ask_or_post(
        bindings=bindings,
        ki_id=bsh_proactive_ssa.bsh_device_metadata_ask_ki_id,
        response_wait_timeout_seconds=BSHConfig.ASK_DEVICE_METADATA_TIMEOUT,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=BSHConfig.ASK_DEVICE_METADATA_SELF_HEAL_TRIES
    )


    # TODO: Handle Exchange Info Status message


    # ---------------------- Convert binding data to useful data for the service ---------------------- #

    if ask_response_code == 200:

        if len(ask_response["exchangeInfo"]) == 0:
            device_metadata = "Ask for Bosch/Miele device metadata failed"
            ask_response_code = 500
            generalLogger.error("SSA communication could not reach Bosch server.")
        else:
            device_metadata = process_bsh_binding_set(ask_response["bindingSet"])[0]
    
    else:
        device_metadata = []
        generalLogger.error(
            f"Ask request was unsuccessful with error code {ask_response_code}.\n" \
            f"Sending empty appliance list...\n"
        )

    generalLogger.info('SSA ASK device metadata completed. Exiting...')

    return device_metadata, ask_response_code
