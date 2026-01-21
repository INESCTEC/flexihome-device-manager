import time, pytz
from datetime import datetime, timezone
from sqlalchemy import func

from energy_manager_service import generalLogger, Config, db
from energy_manager_service.ssa.cybergrid.config import CybergridConfig
from energy_manager_service.ssa.cybergrid.ssa_classes.pt_pilot_reactive import PTPilotReactiveCybergridSSA

from energy_manager_service.clients.hems_services.device_manager import post_request_delay_by_cycle
from energy_manager_service.events.notification_events import loop, send_shift_notification, send_shift_recommendation_notification

from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility, DBOptimizedCycles

from energy_manager_service.utils.date.seconds_to_days_minutes_hours import seconds_to_days_minutes_hours

def bindings_to_json_setpoint(bindings):
    
    dp=bindings[0]['dp'].replace("<", "").replace(">", "")
    dp=dp.split("/")
    dp=dp[len(dp)-1]

    asset = bindings[0]['asset'].replace("<", "").replace(">", "")

    ctv = bindings[0]['ctv'].split("^^")
    ctv = ctv[0].replace("\"", "")

    tisv = bindings[0]['tisv'].split("^^")
    tisv = tisv[0].replace("\"", "")

    tiev = bindings[0]['tiev'].split("^^")
    tiev = tiev[0].replace("\"", "")

    qapv = bindings[0]['qapv'].split("^^")
    qapv = qapv[0].replace("\"", "")

    parsed_parameters = {
        'dp': dp,
        'asset': asset,
        'ctv': ctv,
        'tisv': tisv,
        'tiev': tiev,
        'qapv': qapv
    }

    return parsed_parameters

def setpoint_handle(exitEvent, cybergrid_ssa: PTPilotReactiveCybergridSSA):

    start = time.time()
    total_time = 0
    while not exitEvent.wait(timeout=0.01):

        current_time = time.time()
        if current_time - start >= 600:
            total_time += round(current_time - start)
            seconds_to_days_minutes_hours(total_time)
            start = current_time

        response, ki_id, handle_request_id, binding_set, requesting_kb_id = cybergrid_ssa.handle(
            kb_id=cybergrid_ssa.pt_pilot_reactive_kb_id,
            self_heal=True,
            refresh_kb=CybergridConfig.REACTIVE_KB_REFRESH_TIMER_MINUTES,
            debug=False
        )


        if response.status_code == 200:

            if ki_id != cybergrid_ssa.setpoint_ki_id:
                generalLogger.warning(f"Unexpected binding set received from KI: {ki_id}")
                generalLogger.warning(f"From KB: {requesting_kb_id}\n")
                continue

            generalLogger.debug(f"Data received on handle:\n{binding_set}")

            parsed_json = bindings_to_json_setpoint(binding_set)
            asset = parsed_json['asset']  # Asset with flexibility accepted by aggregator

            response, status_code = cybergrid_ssa.answer_or_react(handle_request_id, [], ki_id)
            generalLogger.info(f"REACT status code: {status_code}")

            
            
            # --------------- Process setpoints received (parsed_json) --------------- #

            # Check if asset (HEMS) offered flexibility today
            user_flex_offers_today = DBAvailableFlexbility.query.filter(
                DBAvailableFlexbility.meter_id == asset,
                func.date(DBAvailableFlexbility.request_datetime) == datetime.now(timezone.utc).date()
            ).order_by(
                DBAvailableFlexbility.request_datetime.asc()
            ).all()
            generalLogger.debug(user_flex_offers_today)
            
            if len(user_flex_offers_today) > 0:
                # Get the asset's latest offer of today
                latest_offer = user_flex_offers_today[-1]
                generalLogger.info(
                    f"Found latest offer of asset {asset} at {latest_offer.request_datetime}"
                )

                if latest_offer.accepted_by_grid == False:    
                    # Query Optimized cycles for the accepted flex offer
                    user_latest_optimized_cycles = DBOptimizedCycles.query.filter_by(
                        flex_id = latest_offer.flex_id,
                        flex_type = "up",
                        accepted_by_user = False
                    ).all()
                    generalLogger.debug(
                        f"Found optimized cycles for flex up for asset {asset}:\n{user_latest_optimized_cycles}"
                    )
                    
                    if user_latest_optimized_cycles is not None:
                        generalLogger.info("Sending delay/notification to accepted cycles")
                        for optimized_cycle in user_latest_optimized_cycles:
                            
                            # Send notification and delay
                            if optimized_cycle.auto_management:
                                # Send delay to device
                                _, status_code = post_request_delay_by_cycle(
                                    latest_offer.user_id,
                                    optimized_cycle.serial_number,
                                    optimized_cycle.sequence_id,
                                    optimized_cycle.optimized_start_time.strftime(Config.TIMESTAMP_FORMAT)
                                )
                                
                                # delay successful
                                if status_code < 300:
                                    # Send notification to asset
                                    scheduled_start_time_notification_format = optimized_cycle.optimized_start_time.astimezone(pytz.timezone(Config.COUNTRY)).strftime("%H:%M")
                                    try:
                                        loop.run_until_complete(
                                            send_shift_notification(
                                                optimized_cycle.serial_number, 
                                                scheduled_start_time_notification_format, 
                                                latest_offer.user_id, 
                                                language = 'PT'  # TODO: Get the language from the user's profile
                                            )
                                        )
                                        optimized_cycle.notification_sent = True
                                    except Exception as e:
                                        generalLogger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}")
                                        optimized_cycle.notification_sent = False

                                    optimized_cycle.accepted_by_user = True
                                    optimized_cycle.delay_call_ok = True
                                    db.session.commit()

                                # Delay failed
                                else:
                                    generalLogger.error(f"Error sending delay to cycle {optimized_cycle.serial_number}")
                                    try:
                                        loop.run_until_complete(
                                            send_shift_recommendation_notification(
                                                optimized_cycle.serial_number,
                                                latest_offer.user_id,
                                                language = 'PT'
                                            )
                                        )
                                        optimized_cycle.notification_sent = True
                                    except Exception as e:
                                        generalLogger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}")
                                        optimized_cycle.notification_sent = False
                                    optimized_cycle.delay_call_ok = False
                                    optimized_cycle.delay_call_description = "Error sending delay to device"
                                    db.session.commit()

                            else:
                                # Send notification only (to asset)
                                try:
                                    loop.run_until_complete(
                                        send_shift_recommendation_notification(
                                            optimized_cycle.serial_number,
                                            latest_offer.user_id,
                                            language = 'PT'
                                        )
                                    )
                                    optimized_cycle.notification_sent = True
                                except Exception as e:
                                    generalLogger.warning(f"Error sending notification to cycle {optimized_cycle.serial_number}: {repr(e)}")
                                    optimized_cycle.notification_sent = False

                            # UPDATE TABLE (available flexibility) ACCEPT COLUMN TO TRUE
                            latest_offer.accepted_by_grid = True
                            db.session.commit()
                        
                    else:
                        generalLogger.error(f"No flex UP optimized cycles found for asset {asset}")
                else:
                    generalLogger.warning(f"Latest flexibility for asset {asset} has already been accepted")
            else:
                generalLogger.error(f"The asset with id {asset} has no flex offers for today")
