import requests, uuid
from datetime import timedelta
from requests.exceptions import ReadTimeout
from requests.models import Response

from energy_manager_service import logger, Config
from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling
from energy_manager_service.clients.common.post import post_with_error_handling


def list_devices(user_ids, x_correlation_id=None):
    if x_correlation_id is None:
        x_correlation_id = {"X-Correlation-ID": str(uuid.uuid4())}
    logger.info(
        f'Calling {Config.HOST_DEVICEMANAGERSERVICE}/device for {user_ids}.',
        extra=x_correlation_id
    )
    
    host = f"{Config.HOST_DEVICEMANAGERSERVICE}/device"
    query_params = {
        'user-ids': user_ids
    }
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
    }
    
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response)

    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_DEVICEMANAGERSERVICE}/device returned status code: {status_code}',
        extra=x_correlation_id
    )
    
    return processed_response, status_code


def get_schedule_cycle_by_user(user_id, start_date, end_date, x_correlation_id):

    logger.info(
        f'Calling {Config.HOST_DEVICEMANAGERSERVICE}/schedule-cycle-by-user for {user_id}" \
            " between {start_date} and {end_date}.',
        extra=x_correlation_id
    )
    
    host = f"{Config.HOST_DEVICEMANAGERSERVICE}/schedule-cycle-by-user"
    query_params = {
        'user_ids': [user_id],
        'start_timestamp': start_date.strftime(Config.TIMESTAMP_FORMAT),
        'end_timestamp':  end_date.strftime(Config.TIMESTAMP_FORMAT)
    }
    
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
    }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)

    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_DEVICEMANAGERSERVICE}/schedule-cycle-by-user " \
            "returned status code: {status_code}',
        extra=x_correlation_id
    )
    
    return processed_response, status_code


def get_settings_by_device(serial_number, x_correlation_id):
    
    logger.info(
        f'Calling {Config.HOST_DEVICEMANAGERSERVICE}/settings-by-device for {serial_number}',
        extra=x_correlation_id
    )
    
    host = f"{Config.HOST_DEVICEMANAGERSERVICE}/settings-by-device"
    query_params = {
        "serial_numbers": [serial_number]
        }
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
        }
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)
    
    
    # Process specific endpoint cases
    # Endpoint returned unexpected format
    try:
        if status_code == 200:
            if (len(processed_response) == 0) or (len(processed_response[0]["settings"]) == 0):
                status_code = 404
                processed_response = {"error": f"Device Manager Get Settings: No settings found for device {serial_number}"}
                logger.error(processed_response["error"], extra=x_correlation_id)
    
    except Exception as e:
        status_code = 400
        processed_response = {"error": f"Device Manager Get Settings: Error processing response: {e}"}
        logger.error(processed_response["error"], extra=x_correlation_id)
    
    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_DEVICEMANAGERSERVICE}/settings-by-device returned status code: {status_code}',
        extra=x_correlation_id
    )                    
    
    return processed_response, status_code


def post_request_delay_by_cycle(user_id, serial_number, sequence_id, new_scheduled_start_time, x_correlation_id=None):
    
    if x_correlation_id is None:
        x_correlation_id = {"X-Correlation-ID": str(uuid.uuid4())}

    logger.info(
        f'Calling {Config.HOST_DEVICEMANAGERSERVICE}/request-delay-by-cycle " \
            "for {sequence_id} of user {user_id}',
        extra=x_correlation_id
    )

    host = f"{Config.HOST_DEVICEMANAGERSERVICE}/request-delay-by-cycle"
    headers = {
        "Content-Type": "application/json",
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
    }
    
    query_params = {
        "user-id" : user_id
    }

    request_body = [{
        "sequence_id": sequence_id,
        "serial_number": serial_number,
        "new_start_time": new_scheduled_start_time
    }]
    
    instantiate_response_object = False
    try:
        response = requests.post(
            host, 
            headers = headers, 
            params = query_params,
            json = request_body,
            timeout=Config.REQUEST_TIMEOUT_SECONDS
        )
    except ReadTimeout as e:
        logger.error(f"Device Manager Request Delay: Timeout error: {repr(e)}", extra=x_correlation_id)
        response = b'{"error": f"Device Manager Request Delay: Timeout error: {repr(e)}"}'
        status_code = 408
        instantiate_response_object = True
    except Exception as e:
        logger.error(f"Device Manager Request Delay: Unexpected error: {repr(e)}", extra=x_correlation_id)
        response = b'{"error": f"Device Manager Request Delay: Unexpected error: {repr(e)}"}'
        status_code = 500
        instantiate_response_object = True
    
    if instantiate_response_object:
        response = Response()
        response._content = response
        response.status_code = status_code
    
    try:
        processed_response, status_code = process_response(response, x_correlation_id)
    except Exception as e:
        logger.error(f"Device Manager Request Delay: Error processing response: {repr(e)}", extra=x_correlation_id)
        processed_response = {"error": f"Device Manager Request Delay: Error processing response: {repr(e)}"}
        status_code = 500

    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_DEVICEMANAGERSERVICE}/request-delay-by-cycle returned status code: {status_code}',
        extra=x_correlation_id
    )
    
    return processed_response, status_code