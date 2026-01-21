# coding: utf-8 
# Version: 2.5
#==============================================================================
#   Interconnect project - Flexibility Manager Service

import uuid, connexion, pytz, traceback
from datetime import datetime, timezone
from typing import List
from sqlalchemy import func

from energy_manager_service import logger, auth, db, Config

from energy_manager_service.models.error import Error

from energy_manager_service.optimizers.scheduler import FlexibilityScheduler
from energy_manager_service.optimizers.optimizer_pipeline import OptimizerPipeline

from energy_manager_service.models.scheduling import Scheduling
from energy_manager_service.models.available_flexibility_response import AvailableFlexibilityResponse

from energy_manager_service.models.flex_accept_body import FlexAcceptBody
from energy_manager_service.models.flex_accepted_acknowledged import FlexAcceptedAcknowledged

from energy_manager_service.models.database.energy_manager_db import (
    DBAvailableFlexbility,
    DBOptimizedCycles
)

from energy_manager_service.clients.hems_services.account_manager import get_user
from energy_manager_service.clients.hems_services.device_manager import post_request_delay_by_cycle
from energy_manager_service.events.notification_events import loop, send_shift_notification, send_shift_recommendation_notification 

from energy_manager_service.ssa.cybergrid.baseline_post_interaction import baseline_post
from energy_manager_service.ssa.cybergrid.upper_limit_post_interaction import upper_limit_post
from energy_manager_service.ssa.cybergrid.lower_limit_post_interaction import lower_limit_post


def logErrorResponse(error, endText, response, cor_id):
    logger.error(error, extra=cor_id)
    logResponse(endText, response, cor_id)
    
def logResponse(endText, response, cor_id):
    logger.info(f"{endText}\n", extra=cor_id)
    if response is not None:
        logger.debug("Sending the following response: ", extra=cor_id)
        logger.debug(f"{response}\n", extra=cor_id)


def flexibility_available_get(user_id):  # noqa: E501
    """Fetch latest flexibility available for &lt;user_id&gt;.

     # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param user_id: 
    :type user_id: str
    :param authorization: 
    :type authorization: str

    :rtype: AvailableFlexibilityResponse
    """
    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}
    end_text = f"Request GET /flexibility/available from {user_id} finished processing."
    logger.info(f"Request GET /flexibility/available from {user_id}", extra=cor_id)

    # Verify request permissions 
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )
    

    user_flex_offers_today = DBAvailableFlexbility.query.filter(
        DBAvailableFlexbility.user_id == user_id,
        func.date(DBAvailableFlexbility.request_datetime) == datetime.now(timezone.utc).date()
    ).order_by(
        DBAvailableFlexbility.request_datetime.asc()
    ).all()
    logger.debug(user_flex_offers_today, extra=cor_id)
    
    if len(user_flex_offers_today) == 0:
        error_message = f"The asset with id {user_id} has no flex offers for today"
        logger.error(error_message, extra=cor_id)
        
        return Error(error_message), 404, cor_id
    
    
    # Get the asset's latest offer of today
    latest_offer = user_flex_offers_today[-1]
    logger.info(
        f"Found latest offer of asset {user_id} at {latest_offer.request_datetime}",
        extra=cor_id
    )
    
    if latest_offer.accepted_by_grid:
        message = f"Latest flexibility for asset {user_id} has already been accepted"
        logger.warning(message, extra=cor_id)
        
        return FlexAcceptedAcknowledged(message), 202, cor_id
        

    logger.info(f"Asset {user_id} has available flexibility - {latest_offer.flex_id}", extra=cor_id)


    # Convert db model to response object
    baseline, flex_up, flex_down = [], [], []
    for item in latest_offer.vectors:
        baseline.append(
            Scheduling(
                start_time = item.timestamp.strftime(Config.TIMESTAMP_FORMAT),
                power_value = item.baseline,
                power_units = "kW"
            )
        )
        flex_up.append(
            Scheduling(
                start_time = item.timestamp.strftime(Config.TIMESTAMP_FORMAT),
                power_value = item.flex_up,
                power_units = "kW"
            )
        )
        flex_down.append(
            Scheduling(
                start_time = item.timestamp.strftime(Config.TIMESTAMP_FORMAT),
                power_value = item.flex_down,
                power_units = "kW"
            )
        )

    response = AvailableFlexibilityResponse(
        user_id=user_id,
        baseline=baseline,
        flexibility_upward=flex_up,
        flexibility_downward=flex_down
    )
    
    return response, 200, cor_id

    
def flexibility_available_post(user_id):
    """Build dayahead energy flexibility considering only appliances in the HEMS pool.
    # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param user_id: 
    :type user_id: str
    :param authorization: 
    :type authorization: str
    :param demo_flag: 
    :type demo_flag: bool

    :rtype: AvailableFlexibilityResponse
    """

    cor_id = {"X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}
    end_text = f"Request POST /flexibility/available from {user_id} finished processing."
    logger.info(f"Starting POST request /flexibility/available from {user_id}.", extra=cor_id)

    # Verify request permissions 
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
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
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )


    # Endpoint logic

    params_opt = OptimizerPipeline(
        user_id = user_id,
        x_correlation_id = cor_id
    )
    #==============================================================================
    # Baseline optimization

    inputs_opt_baseline, inputs_call_status_code, cor_id = params_opt.inputs_call()

    status_code = 200
    response_error_msg = ""
    has_baseline_output = False
    has_flexibility_output = False

    ## Flexibility Module calculation and outputs ##
    if (inputs_call_status_code < 300) and (inputs_call_status_code != 202):
        opt_schedule = FlexibilityScheduler(inputs_opt_baseline)
        outputs_opt_baseline = opt_schedule(cor_id)
    else:
        outputs_opt_baseline = None
        logger.error(inputs_opt_baseline, extra=cor_id)

        status_code = 202
        response_error_msg = "Failed to get inputs for flexibility optimization. " \
            "\nSending flexility outputs with zeros."
    
    if outputs_opt_baseline:
        # Flexibility optimization
        inputs_opt_flexibility, _, cor_id = params_opt.inputs_update(outputs_opt_baseline)
        opt_schedule = FlexibilityScheduler(inputs_opt_flexibility)
        outputs_opt_flexibility = opt_schedule(cor_id)
        has_baseline_output = True
    else:
        outputs_opt_flexibility = None
        logger.error("Unfeasible baseline optimizer result", extra=cor_id)
        logger.debug("Returning zeros for flexibility optimizer...", extra=cor_id)
        outputs_opt_baseline = params_opt.outputs_with_zeros()

        status_code = 202
        if len(response_error_msg) != 0: response_error_msg += "\n"
        response_error_msg += "Unfeasible baseline optimizer result. " \
            "\nSending flexibility outputs with zeros."
    
    if outputs_opt_flexibility is None:
        logger.error("Unfeasible flexibility optimizer result", extra=cor_id)
        logger.debug("Returning zeros for flexibility optimizer...", extra=cor_id)
        outputs_opt_flexibility = params_opt.outputs_with_zeros()

        status_code = 202
        if len(response_error_msg) != 0: response_error_msg += "\n"
        response_error_msg += "Unfeasible flexibility optimizer result. " \
            "\nSending flexibility outputs with zeros."
    else:
        has_flexibility_output = True


    ## Build flexibility object and send to SIF ##
    output_flexibility_response, _, cor_id, flex_id = params_opt.outputs_flexibility(
        outputs_opt_baseline,
        outputs_opt_flexibility,
        has_baseline = has_baseline_output,
        has_flexibility = has_flexibility_output
    )

    if Config.MAINTENANCE_MODE == False:
        # Send upper and baseline to aggregator (SIF)
        try:
            # Get user profile (for external_id)
            user_profile, get_user_status_code = get_user(user_id, cor_id=cor_id)
            user_profile = user_profile[0]
            if get_user_status_code < 300:

                start_date = datetime.strptime(
                    output_flexibility_response['baseline'][0]['start_time'],
                    Config.TIMESTAMP_FORMAT
                )

                # Send baseline
                power_consumed : List[float] = [
                    round(record['power_value'], 2) 
                    for record 
                    in output_flexibility_response['baseline']
                ]
                baseline_call_ok = baseline_post(
                    day=start_date,
                    asset=user_profile['meter_id'],
                    power_values=power_consumed
                )
                
                # Send upper limit
                power_consumed : List[float] = [
                    round(record['power_value'], 2)
                    for record 
                    in output_flexibility_response['flexibility_upward']
                ]
                upper_limit_call_ok = upper_limit_post(
                    day=start_date,
                    asset=user_profile['meter_id'],
                    power_values=power_consumed
                )

                # Send lower limit
                power_consumed : List[float] = [
                    round(record['power_value'], 2)
                    for record 
                    in output_flexibility_response['flexibility_downward']
                ]
                lower_limit_call_ok = lower_limit_post(
                    day=start_date,
                    asset=user_profile['meter_id'],
                    power_values=power_consumed
                )

                flex_by_id = DBAvailableFlexbility.query.filter(
                    DBAvailableFlexbility.flex_id==flex_id
                ).first()
                if flex_by_id:
                    flex_by_id.baseline_call_ok = baseline_call_ok
                    flex_by_id.flex_up_call_ok = upper_limit_call_ok
                    flex_by_id.flex_down_call_ok = lower_limit_call_ok
                    db.session.commit()

            else:
                logger.error(
                    f"GET /user failed (status code: {get_user_status_code})",
                    extra=cor_id
                )
        except Exception as e:
            traceback.print_exc()
            logger.error(
                f"Flex SSA calls failed with exception: {repr(e)}",
                extra=cor_id
            )
    else:
        logger.warning(
            "Maintenance mode is enabled. " \
            "Skipping Flex POST interactions.",
            extra=cor_id
        )


    ## Save optimized cycle outputs to database ##
    # Only save cycles if output is not zeros
    if flex_id is not None and has_baseline_output:
        logger.info("Saving baseline optimized cycles to database...", extra=cor_id)
        _, _, cor_id = params_opt.outputs_cycles(flex_id, "baseline", outputs_opt_baseline.shiftable_cycles_result)
    if flex_id is not None and has_flexibility_output:
        logger.info("Saving flexibility optimized cycles to database...", extra=cor_id)
        _, _, cor_id = params_opt.outputs_cycles(flex_id, "up", outputs_opt_flexibility.shiftable_cycles_result)

    if status_code == 200:
        response = output_flexibility_response
    else:
        response = Error(response_error_msg)

    logger.debug(f"Sending the following response: {response}", extra=cor_id)
    logger.info(end_text, extra=cor_id)

    return response, status_code, cor_id


def flexibility_accept_post(asset):  # noqa: E501
    """Third party accept request for an HEMS (user_id) flexibility offered.

     # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param asset: 
    :type asset: str
    :param flex_accept_body: Array of setpoints with the accepted flexibility for an HEMS (asset).  **Must be an array of 96 positions (intervals of 15 minutes).** 
    :type flex_accept_body: dict | bytes
    :param authorization: 
    :type authorization: str

    :rtype: FlexAcceptedAcknowledged
    """
    if connexion.request.is_json:
        flex_accept_body = FlexAcceptBody.from_dict(connexion.request.get_json())  # noqa: E501
    
    cor_id = {"X-Correlation-ID": uuid.uuid4()}
    end_text = f"Endpoint /flexibility/accept for accepting the " \
    f"flexibility of HEMS with id {asset} finished processing."
    
    logger.info(f"Processing /flexibility/accept request for HEMS with id {asset}.", extra=cor_id)

    # Verify request permissions 
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
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
        
    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
            )
    
    
    # --------------- Check if asset (HEMS) offered flexibility today --------------- #
    
    user_flex_offers_today = DBAvailableFlexbility.query.filter(
        DBAvailableFlexbility.user_id == asset,
        func.date(DBAvailableFlexbility.request_datetime) == datetime.now(timezone.utc).date()
    ).order_by(
        DBAvailableFlexbility.request_datetime.asc()
    ).all()
    logger.debug(user_flex_offers_today, extra=cor_id)
    
    if len(user_flex_offers_today) == 0:
        error_message = f"The asset with id {asset} has no flex offers for today"
        logger.error(error_message, extra=cor_id)
        
        return Error(error_message), 404, cor_id
    
    
    # Get the asset's latest offer of today
    latest_offer = user_flex_offers_today[-1]
    logger.info(
        f"Found latest offer of asset {asset} at {latest_offer.request_datetime}",
        extra=cor_id
    )
    
    if latest_offer.accepted_by_grid:
        message = f"Latest flexibility for asset {asset} has already been accepted"
        logger.warning(message, extra=cor_id)
        
        return FlexAcceptedAcknowledged(message), 202, cor_id
    
    
    # ------------- Query Optimized cycles for the accepted flex offer ------------- #
    
    user_latest_optimized_cycles = DBOptimizedCycles.query.filter_by(
        flex_id = latest_offer.flex_id,
        flex_type = "up",
        accepted_by_user = False
    ).all()
    logger.debug(
        f"Found optimized cycles for flex up for asset {asset}:\n{user_latest_optimized_cycles}",
        extra=cor_id
    )
    
    if user_latest_optimized_cycles is None:
        error_message = f"No flex UP optimized cycles found for asset {asset}"
        logger.error(error_message, extra=cor_id)
        
        return Error(error_message), 404, cor_id

    else:
        
        # SEND DELAY/NOTIFICATION TO CYCLES ACCEPTED BY THE REQUEST BODY
        logger.info("Sending delay/notification to accepted cycles", extra=cor_id)
        for optimized_cycle in user_latest_optimized_cycles:
            if optimized_cycle.auto_management:
                # Send notification and delay
                _, status_code = post_request_delay_by_cycle(
                    asset,
                    optimized_cycle.serial_number,
                    optimized_cycle.sequence_id,
                    optimized_cycle.optimized_start_time.strftime(Config.TIMESTAMP_FORMAT),
                    cor_id
                )
                if status_code >= 300:
                    logger.warning(f"Delay failed for cycle: {optimized_cycle.sequence_id}", extra=cor_id)
                    
                    try:
                        loop.run_until_complete(
                            send_shift_recommendation_notification(
                                optimized_cycle.serial_number,
                                asset,
                                language = 'PT'
                            )
                        )
                        optimized_cycle.notification_sent = True
                    except Exception as e:
                        logger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}", extra=cor_id)
                        optimized_cycle.notification_sent = False

                    optimized_cycle.delay_call_ok = False
                    optimized_cycle.delay_call_description = "Error sending delay to device"

                else:
                    try:
                        scheduled_start_time_notification_format = optimized_cycle.optimized_start_time.astimezone(pytz.timezone(Config.COUNTRY)).strftime("%H:%M")
                        loop.run_until_complete(
                            send_shift_notification(
                                optimized_cycle.serial_number, 
                                scheduled_start_time_notification_format, 
                                asset, 
                                language = 'PT'  # TODO: Get the language from the user's profile
                            )
                        )
                        optimized_cycle.notification_sent = True
                    except Exception as e:
                        logger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}", extra=cor_id)
                        optimized_cycle.notification_sent = False

                    optimized_cycle.delay_call_ok = True
                
                optimized_cycle.accepted_by_user = True
                db.session.commit()
                
            else:
                # Send notification only
                try:
                    loop.run_until_complete(
                        send_shift_recommendation_notification(
                            optimized_cycle.serial_number,
                            asset,
                            language = 'PT'
                        )
                    )
                    optimized_cycle.notification_sent = True
                except Exception as e:
                    logger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}", extra=cor_id)
                    optimized_cycle.notification_sent = False
        
        # UPDATE TABLE (available flexibility) ACCEPT COLUMN TO TRUE
        latest_offer.accepted_by_grid = True
        db.session.commit()
        
        logger.info(
            "The schedule was calculated and the json object was obtained as a result.", 
            extra=cor_id
        )

        return FlexAcceptedAcknowledged(f"Accepted flexibility triggered by asset {asset}"), 200, cor_id
