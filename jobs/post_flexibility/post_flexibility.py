import requests, uuid, json, sys
from datetime import datetime, timezone, timedelta

sys.path.append("..")

from energy_manager_service import Config, generalLogger
from energy_manager_service.models.flexibility.available_flexibility import get_flexibility_to_be_offered


available_flexibility = get_flexibility_to_be_offered(
    date=datetime.now(timezone.utc).date()
)

if len(available_flexibility) == 0:
    generalLogger.info("No flexibility to be offered today")
    sys.exit(0)


if Config.MAINTENANCE_MODE:
    generalLogger.info("MAINTENANCE_MODE is ON. Flexibility will use the HEMS internal aggregator service.")
    

    for flex_to_offer in available_flexibility:
        headers = {
            "X-Correlation-ID": str(uuid.uuid4())
        }
        
        generalLogger.debug(flex_to_offer)
        
        
        request_body = []
        
        for flex_type, flex_parameter in zip(["up", "down", "baseline"], ["flex_up", "flex_down", "baseline"]):
            asset_info = {
                "offer_id": str(flex_to_offer.flex_id),
                "flex_type": flex_type,
                "asset_id": flex_to_offer.user_id,
                "creation_timestamp": datetime.now(timezone.utc).strftime(Config.TIMESTAMP_FORMAT),
                "resolution_minutes": 15,
                "organization": "inesctec"
            }
            
            offer = []
            for vector in flex_to_offer.vectors:
                offer.append({
                    "start_timestamp": vector.timestamp.strftime(Config.TIMESTAMP_FORMAT),
                    "end_timestamp": (vector.timestamp + timedelta(minutes=15)).strftime(Config.TIMESTAMP_FORMAT),
                    "power_value": getattr(vector, flex_parameter)
                })
            
            asset_info['offer'] = offer
            
            request_body.append(asset_info)
        
        
        
        url = f"{Config.HOST_AGGREGATOR}/flexibility/offers"
        
        generalLogger.info(f"Sending request to URL {url}")
        # generalLogger.debug(f"Request body:\n{request_body}")
        
        offers_response = requests.post(
            url=url,
            headers=headers,
            json=request_body
        )
        
        generalLogger.debug(offers_response.content.decode('utf-8'))
            
        if offers_response.status_code == 200:
            generalLogger.info("Offer successfully sent to aggregator")

            try:
                offers_response = json.loads(offers_response.content.decode('utf-8'))
                generalLogger.debug(f"Response from URL {url}:\n{offers_response['accepted']}")
            except Exception as e:
                generalLogger.error(f"Failed to decode response from URL {url}: {repr(e)}")
            
        else:
            generalLogger.warning(f"Failed to send offer {flex_to_offer.flex_id} to aggregator!")

else:
    generalLogger.info(
        "MAINTENANCE_MODE is OFF. Flexibility will use the HEMS external aggregator service (Cybergrid)."
    )

    # TODO: SEND BASELINE TO CYBERGRID
