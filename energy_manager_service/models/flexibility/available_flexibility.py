from sqlalchemy import func
# from datetime import _Date

from energy_manager_service import generalLogger
from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility


def get_flexibility_to_be_offered(date):
    
    # GET LATEST AVAILABLE FLEXIBILITY FOR EVERY USER
    unique_user_ids_with_offers = DBAvailableFlexbility.query.with_entities(
        DBAvailableFlexbility.user_id
    ).distinct()
    
    flexibility_to_offer = []
    for user_id in unique_user_ids_with_offers:
        
        latest_flexibility = DBAvailableFlexbility.query.filter(
            DBAvailableFlexbility.user_id==user_id['user_id'],
            DBAvailableFlexbility.accepted_by_grid==False,  # Not yet accepted
            func.date(DBAvailableFlexbility.request_datetime)==date
        ).order_by(
            DBAvailableFlexbility.request_datetime.desc()
        ).first()
        
        generalLogger.debug(latest_flexibility)
        
        if latest_flexibility is not None:
            flexibility_to_offer.append(latest_flexibility)
    

    return flexibility_to_offer
