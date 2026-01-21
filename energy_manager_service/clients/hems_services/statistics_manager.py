import uuid
from datetime import date

from energy_manager_service import logger, Config
from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling


def get_co2_intensity_forecast(forecast_day : date, x_correlation_id):
    logger.info(
        f'Calling {Config.HOST_STATISTICSERVICE}/ecosignal-forecast for {forecast_day}',
        extra=x_correlation_id
    )

    host = f"{Config.HOST_STATISTICSERVICE}/ecosignal-forecast"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
        } 
    query_params = {
        "forecast_day": forecast_day.strftime(Config.DATE_FORMAT)
        }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)

    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_STATISTICSERVICE}/ecosignal-forecast returned status code: {status_code}',
        extra=x_correlation_id
    )
    
    return processed_response, status_code