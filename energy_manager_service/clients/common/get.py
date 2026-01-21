import requests, uuid

from energy_manager_service import logger, Config


def get_with_error_handling(host, headers, query_params = None, x_correlation_id=None):
    
    if query_params is None:
        query_params = []
    
    if x_correlation_id is None:
        x_correlation_id = {"X-Correlation-ID": str(uuid.uuid4())}
    
    
    try:
        response = requests.get(
            host, 
            headers = headers, 
            params = query_params,
            timeout=Config.REQUEST_TIMEOUT_SECONDS
        )

    except requests.exceptions.ConnectTimeout:
        logger.error(
            f"Request to {host} timed out after {Config.REQUEST_TIMEOUT_SECONDS}.",
            extra=x_correlation_id
        )
        
        # Create an empty response with status code 408
        response = requests.Response()
        response.status_code = 408
        response._content = b'{"error": "Request to ' + bytes(host, 'utf-8') + b' timed out."}'

    except Exception as e:
        logger.error(f"Request to {host} failed:\n{repr(e)}", extra=x_correlation_id)
        
        response = requests.Response()
        response.status_code = 500
        response._content = b'{"error": "Request to ' + bytes(host, 'utf-8') + b' timed out."}'
    
    
    return response
