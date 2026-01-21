import uuid

from device_manager_service import logger, Config
from device_manager_service.clients.common.process_response import process_response
from device_manager_service.clients.common.post import http_request_with_error_handling


def post_flexibility_recommendations_accept(recommendation_id, delay_call_ok, delay_call_description, cor_id):
    
    logger.debug(
        f'EnergyManagerService: Accept flexibility recommendation with id {recommendation_id}',
        extra=cor_id
    )

    host = f"{Config.ENERGY_MANAGER_ENDPOINT}/flexibility/recommendations/accept"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': str(uuid.uuid4())
    }
    
    query_params = {
        "recommendation_id" : recommendation_id
    }

    request_body = {
        "delay_call_ok" : delay_call_ok,
        "delay_call_description" : delay_call_description
    }
    
    
    # Handles timeouts and other possible requests exceptions
    response = http_request_with_error_handling("post", host, headers, query_params, request_body, cor_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, cor_id)

    if (status_code == 404) and (all(word in processed_response["error"].lower() for word in ["recommendation", "does", "not", "exist"])):
        logger.warning(f'Recommendation not found: {recommendation_id}', extra=cor_id)
        status_code = 202
    
    return processed_response, status_code


def delete_recommendation(serial_number, sequence_id, cor_id = None):
    if cor_id is None:
        cor_id = {"X-Correlation-ID": str(uuid.uuid4())}
    
    logger.debug(
        f'EnergyManagerService: Delete recommendation for device {serial_number}' \
        f' and cycle with sequence_id {sequence_id}',
        extra=cor_id
    )

    host = f"{Config.ENERGY_MANAGER_ENDPOINT}/flexibility/recommendations"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': str(uuid.uuid4())
    }
    
    query_params = {
        "serial_number" : serial_number,
        "sequence_id" : sequence_id
    }
    
    
    # Handles timeouts and other possible requests exceptions
    response = http_request_with_error_handling("delete", host, headers, query_params, None, cor_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, cor_id)

    if (status_code == 404) and (all(word in processed_response["error"].lower() for word in ["recommendation", "not", "found"])):
        logger.warning(f'Recommendation not found: {serial_number} {sequence_id}', extra=cor_id)
        status_code = 202
    
    return processed_response, status_code