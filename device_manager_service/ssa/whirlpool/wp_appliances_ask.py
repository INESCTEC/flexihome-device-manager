from device_manager_service import generalLogger, whirlpool_proactive_ssa

from device_manager_service.ssa.ssa_config.wp_config import WPConfig
from device_manager_service.utils.ssa.process_bs import process_whirlpool_binding_set


# Specific Service Adapter logic #

def wp_appliances_ask(token):
    generalLogger.info('Begin WP ASK appliances SSA...')


    # ---------------------- ASK request ---------------------- #

    bindings = [{
        "appliances": "<https://www.example.org/appliances>",
        "playerid": f"\"{WPConfig.PLAYER_ID}\"^^<http://www.w3.org/2001/XMLSchema#string>",
        "token": f"\"{token}\"^^<http://www.w3.org/2001/XMLSchema#string>"
    }]


    generalLogger.info(f"# WP APPLIANCES ASK #\n")

    ask_response, ask_response_code = whirlpool_proactive_ssa.ask_or_post(
        bindings=bindings,
        ki_id=whirlpool_proactive_ssa.ask_appliaces_ki_id,
        response_wait_timeout_seconds=WPConfig.ASK_POST_RESPONSE_TIMEOUT_SECONDS,
        self_heal=True,
        delete_kb_when_self_heal=True,
        self_heal_tries=WPConfig.ASK_POST_SELF_HEAL_TRIES
    )


    # TODO: Handle Exchange Info Status message


    # ---------------------- Convert binding data to useful data for the service ---------------------- #

    if ask_response_code == 200:

        if len(ask_response["exchangeInfo"]) == 0:
            appliance_list = []
            ask_response_code = 500
            generalLogger.error("SSA communication could not reach WP server.")
        else:
            appliance_list = process_whirlpool_binding_set(ask_response["bindingSet"])
    
    else:
        appliance_list = []
        generalLogger.error(
            f"Ask request was unsuccessful with error code {ask_response_code}.\n" \
            f"Sending empty appliance list...\n"
        )

    generalLogger.info('SSA ASK appliances completed. Exiting...')

    return appliance_list, ask_response_code
