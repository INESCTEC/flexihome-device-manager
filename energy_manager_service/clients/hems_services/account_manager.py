import uuid

from energy_manager_service import logger, generalLogger, Config
from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling


def get_user(user_id, cor_id=None):
    if cor_id is None:
        cor_id = {'X-Correlation-ID': str(uuid.uuid4())}
    
    logger.info(
        f'Calling {Config.HOST_ACCOUNTSERVICE}/user for {user_id}',
        extra=cor_id
    )

    host = f"{Config.HOST_ACCOUNTSERVICE}/user"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': cor_id['X-Correlation-ID']
        } 
    query_params = {
        "user-ids": [user_id]
        }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, cor_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, cor_id)

    logger.debug(f'Processed response: {processed_response}', extra=cor_id)
    logger.info(
        f'{Config.HOST_ACCOUNTSERVICE}/user returned status code: {status_code}',
        extra=cor_id
    )

    return processed_response, status_code


def get_all_users(cor_id=None):
    if cor_id is None:
        cor_id =  {'X-Correlation-ID': str(uuid.uuid4())}

    logger.info(f'Calling {Config.HOST_ACCOUNTSERVICE}/user-list', extra=cor_id)

    host = f"{Config.HOST_ACCOUNTSERVICE}/user-list"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': cor_id['X-Correlation-ID']
    }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response)

    logger.debug(f'Processed response: {processed_response}', extra=cor_id)
    logger.info(
        f'{Config.HOST_ACCOUNTSERVICE}/user-list returned status code: {status_code}',
        extra=cor_id
    )
    
    return processed_response, status_code


def list_dongles(cor_id=None):
    if cor_id is None:
        cor_id =  {'X-Correlation-ID': str(uuid.uuid4())}
    
    logger.info(
        f'Calling {Config.HOST_ACCOUNTSERVICE}/list-dongles',
        extra=cor_id
    )
    
    host = f"{Config.HOST_ACCOUNTSERVICE}/list-dongles"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': cor_id['X-Correlation-ID']
    }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response)

    logger.debug(f'Processed response: {processed_response}', extra=cor_id)
    logger.info(
        f'{Config.HOST_ACCOUNTSERVICE}/list-dongles returned status code: {status_code}',
        extra=cor_id
    )
    
    return processed_response, status_code

