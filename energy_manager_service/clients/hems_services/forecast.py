from datetime import timedelta, datetime, timezone

from energy_manager_service import logger, Config
from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling

from energy_manager_service.controllers.default_data import Default_data


def get_measurements(installation_code, start_date, x_correlation_id):

    logger.info(
        f'ForecastService: request endpoint get measurements for installation {installation_code}',
        extra=x_correlation_id
    )
    
    host = f"{Config.HOST_FORECASTSERVICE}/measurements"
    headers = {}
    
    query_params = { 
        'start_date' : start_date.strftime("%Y-%m-%dT%H:%MZ"),
        'end_date' :  (start_date + timedelta(hours=23)).strftime("%Y-%m-%dT%H:%MZ"),
        'installation_code': installation_code
        }
    
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)
    
    return processed_response, status_code


def get_forecast(installation_code, start_date, x_correlation_id):
    
    end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
    # end_date = start_date + timedelta(days=1)
    logger.info(
        f'Calling {Config.HOST_FORECASTSERVICE}/get-forecast for {installation_code}' \
        f'between {start_date} and {end_date}',
        extra=x_correlation_id
    )

    host = f"{Config.HOST_FORECASTSERVICE}/get-forecast"
    headers = {}
    
    query_params = { 
        'start_date' : start_date.strftime("%Y-%m-%dT%H:%MZ"),
        'end_date' :  end_date.strftime("%Y-%m-%dT%H:%MZ"),
        'installation_code': installation_code
        }
    
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)
    
    # Process specific endpoint cases
    # Endpoint returned unexpected format
    valid_response = True
    try:
        if status_code == 200:
            # Forecast has no data for this user at this moment in time
            if len(processed_response["data"]) == 0:
                valid_response = False
                status_code = 404
                processed_response = {"error": "Forecast returned an empty array. Maybe a missing installation"}
                logger.error(processed_response['error'], extra=x_correlation_id)

            # Forecast endpoint returns an array of inconsistent length
            elif len(processed_response["data"][0]["values"]) != 24:
                valid_response = False
                status_code = 400
                processed_response = {"error": f"Error: Forecast returned an array of inconsistent length: {len(processed_response['data'][0]['values'])}"}
                logger.error(processed_response['error'], extra=x_correlation_id)
        else:
            valid_response = False
    
    except Exception as e:
        logger.error(
            f'ForecastService: Error processing response: {e}',
            extra=x_correlation_id
        )
        
        valid_response = False
        status_code = 400
        processed_response = {"error": "Forecast returned data in the wrong format"}
    
    if not valid_response and Config.ACTIVATE_DEFAULT_DATA:
        logger.warning(
            "There was error on the forecast, but default data is activated. Returning default data.",
            extra=x_correlation_id
        )
        status_code = 200
        
        default_data = Default_data()
        values = []
        dt_step = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        creation_time = datetime.now(timezone.utc).strftime(Config.TIMESTAMP_FORMAT)
        for value in default_data.FORECAST_CONSUMPTION:
            values.append({
                "timestamp": dt_step.strftime(Config.TIMESTAMP_FORMAT),
                "creationtime": creation_time,
                "value_p": value,
                "value_q": None
            })

            dt_step += timedelta(minutes=60)

        processed_response = {
            'data': [{
                'installation_type': 'load',
                'installation_code': installation_code,
                'values': values
            }],
            'code': 1
        }            
    
    logger.debug(f"Parsed response: {processed_response}", extra=x_correlation_id)
    logger.info(
        f"{Config.HOST_FORECASTSERVICE}/get-forecast returned status code: {status_code}",
        extra=x_correlation_id
    )

    return processed_response, status_code