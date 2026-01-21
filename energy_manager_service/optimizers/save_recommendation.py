# from datetime import datetime
# import pytz

# from energy_manager_service import logger, db, Config

# from energy_manager_service.models.error import Error
# from energy_manager_service.clients.hems_services.device_manager import post_request_delay_by_cycle
# from energy_manager_service.events.notification_events import loop, send_shift_notification, send_shift_recommendation_notification 

# from energy_manager_service.models.database.energy_manager_db import TableScheduleCycle


# def shift_and_save_recommendation(start_date, user_id, automatic_management, serial_number, sequence_id, new_scheduled_start_time, x_correlation_id):

#     # Update device start time, in case user has set the device has being automatically managed
#     if automatic_management:
#         request_delay_response, status_code = post_request_delay_by_cycle(
#             user_id,
#             serial_number,
#             sequence_id,
#             new_scheduled_start_time,
#             x_correlation_id
#         )
        
#         # TODO: Can we handle this errors inside the clients package?
#         if status_code >= 300:
#             return Error(request_delay_response["error"]), status_code, x_correlation_id
        
#         if len(request_delay_response) == 0:
#             error_msg = f"Request delay response is empty."
#             logger.error(error_msg, extra=x_correlation_id)
            
#             return Error(error_msg), 404, x_correlation_id
        
#         if request_delay_response[0]["delayed"] == False:
#             error_msg = f'The cycle {sequence_id} is indicated to shift, but the request was refused by the manufacturer'
#             logger.warning(error_msg, extra=x_correlation_id)
            
#             return Error(error_msg), 403, x_correlation_id
        
#         else:
#             logger.info(
#                 f'The cycle {sequence_id} is changed. \nNew start_time: {new_scheduled_start_time}.',
#                 extra=x_correlation_id
#             )
    
    
#     # Check if optimized schedule already exists in DB
#     optimized_schedule_in_db = db.session.query(TableScheduleCycle).filter_by(
#         user_id = user_id,
#         serial_number = serial_number,
#         sequence_id = sequence_id,
#         # day_ahead = Config.START_DAY_AHEAD_LOCAL
#         day_ahead = start_date
#     ).first()
    
#     if optimized_schedule_in_db is not None:
#         error_msg = f"The cycle {sequence_id} is already optimized with the same new start time."
#         logger.error(error_msg, extra=x_correlation_id)
        
#         return Error(error_msg), 409, x_correlation_id
    
    
#     # Insert cycle to Database
#     new_scheduled_start_time = datetime.strptime(new_scheduled_start_time, Config.TIMESTAMP_FORMAT)
    
#     data_entry = TableScheduleCycle(
#         user_id=user_id,
#         serial_number=serial_number, 
#         sequence_id=sequence_id,
#         day_ahead=start_date,
#         acceptance_request=automatic_management,
#         shown_in_app=True,
#         scheduled_start_time=new_scheduled_start_time,
#         datetime_requested=datetime.now(),
#         x_correlation_id=str(x_correlation_id)
#     )

#     db.session.add(data_entry)
#     db.session.commit()

#     logger.debug(f'New start time of cycle {sequence_id} data was inserted.', extra=x_correlation_id)
    

#     # Send Notification to HEMS app
#     if automatic_management == True:
#         scheduled_start_time_notification_format = new_scheduled_start_time.astimezone(pytz.timezone(Config.COUNTRY)).strftime("%H:%M")
#         loop.run_until_complete(
#             send_shift_notification(
#                 serial_number, 
#                 scheduled_start_time_notification_format, 
#                 user_id, 
#                 language = 'PT'  # TODO: Get the language from the user's profile
#             )
#         )
        
#     else:
#         loop.run_until_complete(
#             send_shift_recommendation_notification(
#                 serial_number,
#                 user_id,
#                 language = 'PT'
#             )
#         )
    
#     return None, 200, None