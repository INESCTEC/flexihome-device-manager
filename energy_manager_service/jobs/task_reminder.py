# import uuid, uuid, pytz
# from datetime import datetime, timedelta
# from types import SimpleNamespace

# from energy_manager_service import logger, Config
# from energy_manager_service.events.notification_events import loop, send_shift_notification

# from energy_manager_service.models.database.energy_manager_db import TableScheduleCycle


# def remind_user_of_pending_recommendations(user_id) -> bool:
    
#     cor_id = {"X-Correlation-ID": uuid.uuid4()}
#     logger.info(f"The endpoint cycle_data_get is requested by {user_id}", extra=cor_id)
    
#     # Get data cycles
#     try:
        
#         data_output = TableScheduleCycle.query.filter_by(
#             user_id=user_id,
#             day_ahead = (datetime.now() + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0),
#             shown_in_app = True
#             ).all()
        
#         result = SimpleNamespace()  # TODO: Este result não está a ser usado??
#         for row in data_output:
#             result.user_id              = row.user_id
#             result.serial_number        = row.serial_number
#             result.sequence_id          = row.sequence_id
#             result.day_ahead            = row.day_ahead
#             result.shown_in_app         = row.shown_in_app
#             result.acceptance_request   = row.acceptance_request
#             result.scheduled_start_time = row.scheduled_start_time
#             result.datetime_requested   = row.datetime_requested
#             result.x_correlation_id_query = row.x_correlation_id

#             # Send Notification to HEMS app
#             scheduled_start_time_notification_format = row.scheduled_start_time.astimezone(pytz.timezone(Config.COUNTRY)).strftime("%H:%M")
            
#             # TODO: Task reminder notification not implemented yet
#             loop.run_until_complete(
#                 send_shift_notification(
#                 row.serial_number, 
#                 scheduled_start_time_notification_format, 
#                 user_id, 
#                 language = 'PT')
#                 )

#             logger.debug(f'The {user_id} cycles data was collected.', extra=cor_id)

#     except Exception as ErrorCodes:
#         logger.error("Import info to DB %s "%(str(ErrorCodes).replace("'","")), extra=cor_id)

#         # Send Notification to HEMS app
#         scheduled_start_time_notification_format = row.scheduled_start_time.astimezone(pytz.timezone(Config.COUNTRY)).strftime("%H:%M")

#         # TODO: Task reminder notification not implemented yet
#         loop.run_until_complete(
#             send_shift_notification(
#             row.serial_number, 
#             scheduled_start_time_notification_format, 
#             user_id, 
#             language = 'PT')
#             )