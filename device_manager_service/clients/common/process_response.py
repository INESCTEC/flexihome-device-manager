import requests, json, uuid

from device_manager_service import logger


def process_response(r : requests.Response, cor_id = None):

    logger.debug(f'Response content: {r.content}', extra=cor_id)
    
    if cor_id is None:
        cor_id = {"X-Correlation-ID": str(uuid.uuid4())}

    # Happy flow
    if 200 <= r.status_code < 210:
        try:
            processed_response = json.loads(r.content.decode('utf-8'))
        except Exception as e:
            logger.warning(f'Could not parse response: {e}', extra=cor_id)
            processed_response = {"error": repr(e)}
            
        logger.debug(f'Response status code: {r.status_code}', extra=cor_id)
        logger.debug(processed_response, extra=cor_id)
        
        return processed_response, r.status_code
    
    # Non happy flow
    elif 400 <= r.status_code < 500:
        try:
            processed_response = json.loads(r.content.decode('utf-8'))
            if isinstance(processed_response, str):
                logger.error(processed_response, extra=cor_id)
                processed_response = {"error": processed_response}
            else:
                logger.error(processed_response["error"], extra=cor_id)
        except Exception as e:
            logger.warning(f'Could not parse response: {e}', extra=cor_id)
            processed_response = {"error": repr(e)}
            
        logger.debug(f'Response status code: {r.status_code}', extra=cor_id)
        logger.debug(processed_response, extra=cor_id)
        
        return processed_response, r.status_code
        
    
    # Unexpected behavior
    else:
        logger.error(f'Could not process response. Unknown error code: {r.status_code}', extra=cor_id)
        r.raise_for_status()
