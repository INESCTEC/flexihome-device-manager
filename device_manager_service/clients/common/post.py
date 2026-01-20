import requests

from device_manager_service import logger, Config


def http_request_with_error_handling(method, host, headers, query_params, request_body, x_correlation_id):
    
    try:
        if method == "post":
            response = requests.post(
                host, 
                headers = headers, 
                params = query_params,
                json = request_body,
                timeout=Config.REQUEST_TIMEOUT_SECONDS
            )
        elif method == "delete":
            response = requests.delete(
                host, 
                headers = headers, 
                params = query_params,
                json = request_body,
                timeout=Config.REQUEST_TIMEOUT_SECONDS
            )
        else:
            raise Exception("Method not supported")

    except requests.exceptions.ConnectTimeout:
        logger.error(
            f"Request to {host} timed out after {Config.REQUEST_TIMEOUT_SECONDS}.",
            extra=x_correlation_id
        )
        
        # Create an empty response with status code 408
        response = requests.Response()
        response.status_code = 408
        response._content = b'{"error": "Request to ' + host + ' timed out."}'

    except Exception as e:
        logger.error(f"Request to {host} failed:\n{repr(e)}", extra=x_correlation_id)
        
        response = requests.Response()
        response.status_code = 500
        response.content = b'{"error": "Request to ' + host + ' timed out."}'
    
    
    return response