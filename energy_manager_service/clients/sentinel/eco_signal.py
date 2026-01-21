from datetime import timedelta

from energy_manager_service import logger, Config
from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling
from energy_manager_service.controllers.default_data import Default_data


def get_forecast_co2intensity(start_date, x_correlation_id, geo_id = Config.GEO_ID):
    
    logger.debug('EcoSignalSentinel: Get CO2 forecast', extra=x_correlation_id)
    
    host = f"{Config.HOST_SENTINEL}/forecast/co2-intensity"
    headers = {
        'accept': 'application/json', 
        'Authorization': Config.SENTINEL_TOKEN,
        'X-CSRFToken': Config.X_CSRFTOKEN
    } 
    
    query_params = {
        "geo_id": geo_id,
        'start_date' : start_date.strftime(Config.TIMESTAMP_FORMAT),
        'end_date' : (start_date + timedelta(days=1)).strftime(Config.TIMESTAMP_FORMAT)
    }
    
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)
    
    
    try:
        if status_code == 200:
            if len(processed_response["data"]) == 0:
                status_code = 404
                processed_response = {"error": f"Error: Eco signal forecast not available for {start_date}"}
                logger.error(processed_response['error'], extra=x_correlation_id)
    
    except Exception as e:
        logger.error(
            f'Sentinel Get CO2: Error processing response: {e}',
            extra=x_correlation_id
        )
        
        status_code = 400
        processed_response = {"error": "Sentinel get CO2 returned data in the wrong format"}
    
    if status_code != 200 and Config.DEMO_MODE:
        logger.warning("DEMO MODE: Using default data", extra=x_correlation_id)
        dd = Default_data(mock_sentinel_api_response=True)
        
        processed_response = dd.CO2_EMISSION
        status_code = 200
    
    return processed_response, status_code