import uuid
from datetime import timedelta, datetime

from energy_manager_service import logger, Config

from energy_manager_service.clients.common.process_response import process_response
from energy_manager_service.clients.common.get import get_with_error_handling



def get_energy_prices_SU(start_date, tarif_type, contracted_power_value, x_correlation_id):
    
    logger.info(
        f'EnergyPricesService: request endpoint get_energy_prices_SU from date {start_date} onwards',
        extra=x_correlation_id
    )
    logger.debug(f"Tariff type: {tarif_type}", extra=x_correlation_id)
    logger.debug(f"Contracted power value: {contracted_power_value}", extra=x_correlation_id)

    if (contracted_power_value <= 20.7):
        endpoint_name = f'SU/{Config.CONSUMER_TYPE}/low-contracted-power' 
    elif (contracted_power_value > 20.7):
        endpoint_name = f'SU/{Config.CONSUMER_TYPE}/high-contracted-power'
    
    
    host = f"{Config.HOST_ENERGYPRICESSERVICE}/{endpoint_name}"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': str(uuid.uuid4())
        }        
    
    end_date = (start_date + timedelta(days=1))
    query_params = {
        'price_type' : Config.PRICE_TYPE, 
        'start_date' : start_date.isoformat(), 
        'end_date' :  end_date.isoformat(), 
        'contracted_power' : contracted_power_value, 
        'tarif_type' : tarif_type
        }

    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)
    
    
    # Process specific endpoint cases
    # Endpoint returned unexpected format
    try:
        if status_code == 200:
            if (len(processed_response["active_energy"]["prices"]) == 0) or (len(processed_response["standing_charges"]["prices"]) == 0):
                logger.error(
                    f'EnergyPricesService: No prices found between {start_date} and {end_date}',
                    extra=x_correlation_id
                )
                
                status_code = 404
                processed_response = {"error": f"No prices found between {start_date} and {end_date}"}
            
            elif (len(processed_response["active_energy"]["prices"]) != 96) or (len(processed_response["standing_charges"]["prices"]) != 96):
                logger.error(
                    f'EnergyPricesService: Prices between {start_date} and {end_date} are in the wrong format',
                    extra=x_correlation_id
                )
                
                status_code = 400
                processed_response = {"error": "Energy Prices returned data in the wrong format"}
                
    except Exception as e:
        logger.error(
            f'EnergyPricesService: Error processing response: {e}',
            extra=x_correlation_id
        )
        
        status_code = 400
        processed_response = {"error": "Energy Prices returned data in the wrong format"}
        
    
    logger.debug(status_code, extra=x_correlation_id)
    logger.debug(processed_response, extra=x_correlation_id)
    
    return processed_response, status_code


def get_tarif_periods_erse(start_time: datetime, tarif_type, x_correlation_id):

    # log_message = 'EnergyPricesService: request endpoint tarif_periods_erse.'
    logger.info(
        f'Calling {Config.HOST_ENERGYPRICESSERVICE}/tariff-periods-erse for {start_time} ' \
        f'and tarif {tarif_type}',
        extra=x_correlation_id
    )
    
    if tarif_type == "bi-hourly":
        tarif_type = "bi-hourly-daily"
    elif tarif_type == "tri-hourly":
        tarif_type = "tri-hourly-daily"


    host = f"{Config.HOST_ENERGYPRICESSERVICE}/tariff-periods-erse"
    headers = {
        'accept': 'application/json', 
        'X-Correlation-ID': x_correlation_id['X-Correlation-ID']
        }
    
    query_params = {
        'start_timestamp' : start_time.replace(hour=0, minute=0, second=0).strftime(Config.TIMESTAMP_FORMAT),
        'end_timestamp' :  start_time.replace(hour=23, minute=59, second=59).strftime(Config.TIMESTAMP_FORMAT),
        'tariff_type' : tarif_type
    } 
    
    # Handles timeouts and other possible requests exceptions
    response = get_with_error_handling(host, headers, query_params, x_correlation_id)
    
    # Process response into a http response ready format for the service api
    processed_response, status_code = process_response(response, x_correlation_id)

    logger.debug(f'Processed response: {processed_response}', extra=x_correlation_id)
    logger.info(
        f'{Config.HOST_ENERGYPRICESSERVICE}/tariff-periods-erse returned status code: {status_code}',
        extra=x_correlation_id
    )
    
    return processed_response, status_code