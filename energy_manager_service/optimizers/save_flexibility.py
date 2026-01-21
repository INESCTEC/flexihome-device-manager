from datetime import datetime, timezone

from energy_manager_service import logger, db
from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility, DBFlexibilityVectors
from energy_manager_service.clients.hems_services.account_manager import get_user



def save_available_flexibility(user_id, baseline, flexibility_downward, flexibility_upward, has_baseline, has_flexibility, x_correlation_id):

    logger.info(f'Saving available flexibility for user {user_id}...', extra=x_correlation_id)
    user_profile, status_code = get_user(user_id, x_correlation_id)
    if status_code < 300:
        asset = user_profile[0]['meter_id']



        logger.debug(baseline, extra=x_correlation_id)
        logger.debug(flexibility_downward, extra=x_correlation_id)
        logger.debug(flexibility_upward, extra=x_correlation_id)

        # Insert data into Database
        db_vectors = []
        if has_baseline or has_flexibility:
            for base_value, flex_up_value, flex_down_value in zip(baseline, flexibility_upward, flexibility_downward):
                base_ts, base_val = base_value.popitem()
                _, flex_up_val = flex_up_value.popitem()
                _, flex_down_val = flex_down_value.popitem()
                
                db_vectors.append(DBFlexibilityVectors(
                    timestamp=base_ts,
                    baseline=base_val,
                    flex_up=flex_up_val,
                    flex_down=flex_down_val
                ))
        else:
            logger.warning(
                'No flexibility vectors saved. Only saving available flexibility.',
                extra=x_correlation_id
            )
        
        db_available_flexibility = DBAvailableFlexbility(
            user_id=user_id,
            meter_id=asset,
            request_datetime=datetime.now(timezone.utc),
            accepted_by_grid=False,
            vectors=db_vectors,
            baseline_zeros=(not has_baseline),
            flex_up_zeros=(not has_flexibility)
        )
        
        db.session.add(db_available_flexibility)
        db.session.commit()

        logger.debug(f'The baseline, flexibility upward and downward data was inserted.', extra=x_correlation_id)
    
    else:
        logger.error(f'Error getting user profile. Status code: {status_code}', extra=x_correlation_id)
        raise Exception(f'Error getting user profile. Status code: {status_code}')
    
    
    return db_available_flexibility.flex_id, asset
