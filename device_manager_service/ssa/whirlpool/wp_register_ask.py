from device_manager_service import generalLogger, whirlpool_proactive_ssa
from device_manager_service.utils.ssa.process_bs import process_whirlpool_binding_set

from device_manager_service.ssa.ssa_config.wp_config import WPConfig


# Specific Service Adapter logic #

def wp_register_ask(token, device_address, register="true"):
    generalLogger.info('Begin WP register appliance ASK SSA...')

    # ---------------------- ASK request ---------------------- #

    bindings = [{
        "deviceAddress": f"\"{device_address}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "register": "<https://www.example.org/register>",
        "playerid": f"\"{WPConfig.PLAYER_ID}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "token": f"\"{token}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "registered": f"\"{register}\"^^<http://www.w3.org/2001/XMLSchema#boolean>"  # NOTE: Can change registered to "false" when user removes "allow access" to HEMS
    }]

    generalLogger.info("# WP APPLIANCES REGISTER ASK #\n")

    ask_response, ask_response_code = whirlpool_proactive_ssa.ask_or_post(
        bindings=bindings,
        ki_id=whirlpool_proactive_ssa.ask_register_ki_id,
        response_wait_timeout_seconds=WPConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=WPConfig.ASK_POST_SELF_HEAL_TRIES
    )


    # TODO: Handle Exchange Info Status message


    # ---------------------- Convert binding data to useful data for the service ---------------------- #
    
    if ask_response_code == 200:

        if len(ask_response["exchangeInfo"]) == 0:
            response = "Failed to register appliance"
            ask_response_code = 500
            generalLogger.error("SSA communication could not reach WP server.")
        
        else:
            registered_appliances = process_whirlpool_binding_set(ask_response["bindingSet"])

            if len(registered_appliances) > 0:
                response = registered_appliances[0]
            else:
                response = "No appliances registered"

        generalLogger.info(f"Whirlpool ASK Register Appliance Response:\n{response}\n")

    
    else:
        response = "Failed to register appliance"
        generalLogger.error(
            f"Ask request was unsuccessful with error code {ask_response_code}.\n" \
            f"Sending empty registered appliance (no appliance was registered)...\n"
        )

    generalLogger.info('SSA register appliance request complete. Exiting...')

    return response, ask_response_code
