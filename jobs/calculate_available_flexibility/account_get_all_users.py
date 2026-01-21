import requests, uuid, json

from config import Config, generalLogger

def process_response(r : requests.Response):
    # Happy flow
    if 200 <= r.status_code < 210:
        try:
            processed_response = json.loads(r.content.decode('utf-8'))
        except Exception as e:
            generalLogger.warning(f'Could not parse response: {e}')
            processed_response = {"error": repr(e)}
            
        generalLogger.debug(f'Response status code: {r.status_code}')
        generalLogger.debug(processed_response)
        
        return processed_response, r.status_code
    
    # Non happy flow
    elif 400 <= r.status_code < 500:
        try:
            processed_response = json.loads(r.content.decode('utf-8'))
            generalLogger.error(processed_response["error"])
        except Exception as e:
            generalLogger.warning(f'Could not parse response: {e}')
            processed_response = {"error": repr(e)}
            
        generalLogger.debug(f'Response status code: {r.status_code}')
        generalLogger.debug(processed_response)
        
        return processed_response, r.status_code
        
    
    # Unexpected behavior
    else:
        generalLogger.error(f'Could not process response. Unknown error code: {r.status_code}')
        r.raise_for_status()


def get_with_error_handling(host, headers, query_params = None):
    
    if query_params is None:
        query_params = []
    
    try:
        response = requests.get(
            host, 
            headers = headers, 
            params = query_params,
            timeout=Config.REQUEST_TIMEOUT_SECONDS
        )

    except requests.exceptions.ConnectTimeout:
        generalLogger.error(
            f"Request to {host} timed out after {Config.REQUEST_TIMEOUT_SECONDS}."
        )
        
        # Create an empty response with status code 408
        response = requests.Response()
        response.status_code = 408
        response._content = b'{"error": "Request to ' + bytes(host, 'utf-8') + b' timed out."}'

    except Exception as e:
        generalLogger.error(f"Request to {host} failed:\n{repr(e)}")
        
        response = requests.Response()
        response.status_code = 500
        response._content = b'{"error": "Request to ' + bytes(host, 'utf-8') + b' timed out."}'
    
    
    return response


def get_all_users():

    generalLogger.info(f'Calling {Config.HOST_ACCOUNTSERVICE}/user-list')

    host = f"{Config.HOST_ACCOUNTSERVICE}/user-list"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': str(uuid.uuid4())
    }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response)

    generalLogger.debug(f'Processed response: {processed_response}')
    generalLogger.info(
        f'{Config.HOST_ACCOUNTSERVICE}/user-list returned status code: {status_code}'
    )
    
    return processed_response, status_code