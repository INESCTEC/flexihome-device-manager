import connexion
from datetime import datetime, timezone, timedelta
from typing import List

from energy_manager_service import auth, logger, db

from energy_manager_service.models.error import Error  # noqa: E501
from energy_manager_service.models.flex_accepted_acknowledged import FlexAcceptedAcknowledged  # noqa: E501

from energy_manager_service.models.recommendation_object import RecommendationObject  # noqa: E501
from energy_manager_service.models.delay_status_body import DelayStatusBody  # noqa: E501

from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility, DBOptimizedCycles


def logErrorResponse(error, endText, response, cor_id):
    logger.error(error, extra=cor_id)
    logResponse(endText, response, cor_id)


def logResponse(endText, response, cor_id):
    logger.info(f"{endText}\n", extra=cor_id)
    if response is not None:
        logger.debug("Sending the following response: ", extra=cor_id)
        logger.debug(f"{response}\n", extra=cor_id)


def flexibility_recommendations_accept_post(recommendation_id):  # noqa: E501
    """User accepts the recommendation for the cycle &lt;sequence_id&gt;

     # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param serial_number: 
    :type serial_number: str
    :param sequence_id: 
    :type sequence_id: str
    :param authorization: 
    :type authorization: str

    :rtype: str
    """
    if connexion.request.is_json:
        delay_status_body = DelayStatusBody.from_dict(
            connexion.request.get_json())

    cor_id = {
        "X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}
    end_text = f"Request /flexibility/recommendations/accept for recommendation {recommendation_id} finished processing"
    logger.info(
        f"Request /flexibility/recommendations/accept for recommendation {recommendation_id}", extra=cor_id)

    # Verify request permissions
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, auth_code, cor_id

    elif auth_code == 200 and auth_response is not None:
        logger.info(
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
        )

    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
        )

    # Verify if recommendation exists
    recommendation = DBOptimizedCycles.query.filter_by(id=recommendation_id, cycle_cancelled_before_activation=False).filter(
        DBOptimizedCycles.optimized_start_time >= datetime.now(timezone.utc)).first()
    if recommendation is None:
        logger.error(
            f"Recommendation {recommendation_id} does not exist.", extra=cor_id)
        msg = f"Recommendation {recommendation_id} does not exist."
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, 404, cor_id

    elif auth_code == 200 and auth_response is not None:
        flex = DBAvailableFlexbility.query.filter_by(
            flex_id=recommendation.flex_id).first()

        if flex.user_id != auth_response:
            logger.warning(
                f"User {auth_response} tried to access other users optimized cycles!",
                extra=cor_id
            )
            msg = "Unauthorized Action!"
            response = Error(msg)
            logErrorResponse(msg, end_text, response, cor_id)

            return response, 403, cor_id

    # Verify if recommendation is already accepted
    if recommendation.accepted_by_user:
        msg = f"Recommendation {recommendation_id} is already accepted."
        logger.error(msg, extra=cor_id)

        return FlexAcceptedAcknowledged(msg), 202, cor_id

    # Accept recommendation
    try:
        recommendation.accepted_by_user = True
        recommendation.delay_call_ok = delay_status_body.delay_call_ok
        if not delay_status_body.delay_call_ok:
            recommendation.delay_call_description = delay_status_body.delay_call_description
        db.session.commit()
        logger.info(
            f"Recommendation {recommendation_id} accepted.", extra=cor_id)

    except Exception as e:
        db.session.rollback()
        msg = f"Error accepting recommendation {recommendation_id}: {e}"
        logger.error(msg, extra=cor_id)
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, 500, cor_id

    return f"Recommendation {recommendation_id} was accepted by the user", 200, cor_id


def flexibility_recommendations_get(user_id, accepted=None):  # noqa: E501
    """Gather optimized cycle recommendations by user from today onward

     # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param user_id: 
    :type user_id: str
    :param authorization: 
    :type authorization: str
    :param accepted: If true, only recommendations accepted by the user will be returned. If false, only recommendations not accepted by the user will be returned. If not present, all recommendations will be returned.
    :type accepted: bool

    :rtype: List[RecommendationObject]
    """
    cor_id = {
        "X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}
    end_text = f"Request GET /flexibility/recommendations from {user_id} finished processing."
    logger.info(
        f"Request GET /flexibility/recommendations from {user_id}", extra=cor_id)
    logger.debug(f"Accepted: {accepted}", extra=cor_id)

    # Verify request permissions
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, auth_code, cor_id

    elif auth_code == 200 and auth_response is not None:
        logger.info(
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
        )

        if user_id != auth_response:
            logger.error(
                f"User {auth_response} trying to access different user devices ({user_id})",
                extra=cor_id
            )

            msg = "Unauthorized action!"
            response = Error(msg)

            logErrorResponse(msg, end_text, response, cor_id)
            return response, 403, cor_id

    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
        )

    time_interval_start = datetime.now(
        timezone.utc).replace(hour=0, minute=0, second=0)
    time_interval_end = time_interval_start + timedelta(days=3)

    user_available_flex = DBAvailableFlexbility.query.filter_by(
        user_id=user_id
    ).all()
    if user_available_flex is not None:
        logger.debug(
            f"Available Flexibilities for user {user_id}: {len(user_available_flex)}",
            extra=cor_id
        )

    if (user_available_flex is None) or (len(user_available_flex) == 0):
        logger.info(
            f"No available flexibility for user {user_id}",
            extra=cor_id
        )
        return f"No available flexibility for user {user_id}", 202, cor_id

    # Optimized cycles between time interval for user flex ids and according to accepted parameter
    user_recommendations = []
    for user_flex in user_available_flex:
        if user_flex.accepted_by_grid:
            flex_type = "up"
        else:
            flex_type = "baseline"

        if accepted is not None:
            user_optimized_cycles: List[DBOptimizedCycles] = DBOptimizedCycles.query.filter(
                DBOptimizedCycles.flex_id == user_flex.flex_id
            ).filter(
                DBOptimizedCycles.flex_type == flex_type
            ).filter(
                DBOptimizedCycles.optimized_start_time >= time_interval_start
            ).filter(
                DBOptimizedCycles.optimized_end_time <= time_interval_end
            ).filter(
                DBOptimizedCycles.accepted_by_user == accepted
            ).filter(
                DBOptimizedCycles.cycle_cancelled_before_activation == False
            ).all()
        else:
            user_optimized_cycles: List[DBOptimizedCycles] = DBOptimizedCycles.query.filter(
                DBOptimizedCycles.flex_id == user_flex.flex_id
            ).filter(
                DBOptimizedCycles.flex_type == flex_type
            ).filter(
                DBOptimizedCycles.optimized_start_time >= time_interval_start
            ).filter(
                DBOptimizedCycles.optimized_end_time <= time_interval_end
            ).filter(
                DBOptimizedCycles.cycle_cancelled_before_activation == False
            ).all()

        logger.debug(
            f"Optimized cycles query results:\n{user_optimized_cycles}", extra=cor_id)

        if user_optimized_cycles is not None:
            for recommendation in user_optimized_cycles:
                if recommendation.accepted_by_user == False:
                    if recommendation.optimized_start_time.astimezone(tz=None) <= datetime.now(timezone.utc):
                        logger.warning(
                            "Found a recommendation that is not accepted and has already expired."
                            " Ignoring it.",
                            extra=cor_id
                        )
                        continue

                user_recommendations.append(recommendation)

    if len(user_recommendations) != 0:
        logger.debug(
            f"Optimized cycles for user {user_id}: {len(user_recommendations)}",
            extra=cor_id
        )
    else:
        logger.info(
            f"No optimized cycles for user {user_id} for the next 3 days",
            extra=cor_id
        )
        return f"No optimized cycles for user {user_id}", 202, cor_id

    # Serialize response
    response = []
    for optimized_cycle in user_recommendations:
        response.append(
            RecommendationObject(
                recommendation_id=optimized_cycle.id,
                sequence_id=optimized_cycle.sequence_id,
                serial_number=optimized_cycle.serial_number,
                optimized_start_time=optimized_cycle.optimized_start_time,
                optimized_end_time=optimized_cycle.optimized_end_time,
                accepted=optimized_cycle.accepted_by_user
            )
        )

    return response, 200, cor_id


def flexibility_recommendations_delete(recommendation_id=None, sequence_id=None, serial_number=None):  # noqa: E501
    """Delete recommendation by id or by sequence id

    MUST CONTAIN EITHER THE <recommendation_id> OR BOTH THE <sequence_id> AND <serial_number> # noqa: E501

    :param x_correlation_id: 
    :type x_correlation_id: 
    :param authorization: 
    :type authorization: str
    :param recommendation_id: 
    :type recommendation_id: int
    :param sequence_id: 
    :type sequence_id: str
    :param serial_number: 
    :type serial_number: str

    :rtype: str
    """
    cor_id = {
        "X-Correlation-ID": connexion.request.headers["X-Correlation-ID"]}
    end_text = f"Request DELETE /flexibility/recommendations finished processing."
    logger.info(f"Request DELETE /flexibility/recommendations", extra=cor_id)

    logger.debug(f"Recommendation ID: {recommendation_id}", extra=cor_id)
    logger.debug(f"Sequence ID: {sequence_id}", extra=cor_id)
    logger.debug(f"Serial Number: {serial_number}", extra=cor_id)

    # Check if either the recommendation ID or both the sequence ID and serial number exist
    if (recommendation_id is not None) and (sequence_id is None) and (serial_number is None):
        pass
    elif (sequence_id is not None) and (serial_number is not None) and (recommendation_id is None):
        pass
    else:
        msg = "Invalid request. Must contain either the recommendation ID or both the sequence ID and serial number."
        logger.error(msg, extra=cor_id)
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, 400, cor_id

    # Verify request permissions
    auth_response, auth_code = auth.verify_basic_authorization(
        connexion.request.headers
    )

    if (auth_code != 200):
        logger.error(auth_response, extra=cor_id)
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        logErrorResponse(msg, end_text, response, cor_id)

        return response, auth_code, cor_id

    elif auth_code == 200 and auth_response is not None:
        logger.info(
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
        )

    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
        )

    # Delete recommendation based on recommendation id
    if recommendation_id:
        recommendation = DBOptimizedCycles.query.filter_by(
            id=recommendation_id, cycle_cancelled_before_activation=False).first()

        if recommendation is not None:
            if auth_code == 200 and auth_response is not None:

                flex = DBAvailableFlexbility.query.filter_by(
                    flex_id=recommendation.flex_id).first()

                if flex.user_id != auth_response:
                    logger.warning(
                        f"User {auth_response} tried to access other users optimized cycles!",
                        extra=cor_id
                    )
                    msg = "Unauthorized Action!"
                    response = Error(msg)
                    logErrorResponse(msg, end_text, response, cor_id)

                    return response, 403, cor_id

        if recommendation is None:
            msg = f"Recommendation {recommendation_id} not found."
            logger.error(msg, extra=cor_id)
            response = Error(msg)
            logErrorResponse(msg, end_text, response, cor_id)

            return response, 404, cor_id

        try:
            # db.session.delete(recommendation)
            recommendation.cycle_cancelled_before_activation = True
            db.session.commit()
            logger.info(
                f"Recommendation {recommendation_id} deleted.", extra=cor_id)

        except Exception as e:
            db.session.rollback()
            msg = f"Error deleting recommendation {recommendation_id}: {e}"
            logger.error(msg, extra=cor_id)
            response = Error(msg)
            logErrorResponse(msg, end_text, response, cor_id)

            return response, 500, cor_id

        response = f"Recommendation {recommendation_id} deleted."
        return_code = 200

    # Delete recommendation based on sequence id and serial number
    else:
        recommendations = DBOptimizedCycles.query.filter_by(
            sequence_id=sequence_id,
            serial_number=serial_number,
            cycle_cancelled_before_activation=False
        ).all()
        if len(recommendations) == 0:
            msg = f"Recommendations of {sequence_id} for device {serial_number} not found."
            logger.error(msg, extra=cor_id)
            response = Error(msg)
            logErrorResponse(msg, end_text, response, cor_id)

            return response, 404, cor_id

        try:
            deleted_recommendations = 0
            for recommendation in recommendations:
                # db.session.delete(recommendation)
                if auth_code == 200 and auth_response is not None:

                    flex = DBAvailableFlexbility.query.filter_by(
                        flex_id=recommendation.flex_id).first()

                    if flex.user_id != auth_response:
                        logger.warning(
                            f"User {auth_response} tried to access other users optimized cycles!",
                            extra=cor_id
                        )
                        continue
                        # msg = "Unauthorized Action!"
                        # response = Error(msg)
                        # logErrorResponse(msg, end_text, response, cor_id)

                        # return response, 403, cor_id

                recommendation.cycle_cancelled_before_activation = True
                deleted_recommendations = deleted_recommendations + 1
            db.session.commit()
            logger.info(
                f"{deleted_recommendations} recommendations for {sequence_id} of device {serial_number} deleted.",
                extra=cor_id
            )

        except Exception as e:
            db.session.rollback()
            msg = f"Error deleting recommendations of {sequence_id} for device {serial_number}: {e}"
            logger.error(msg, extra=cor_id)
            response = Error(msg)
            logErrorResponse(msg, end_text, response, cor_id)

            return response, 500, cor_id

        if deleted_recommendations == 0:
            response = f"Recommendations of {sequence_id} for device {serial_number} not found."
            return_code = 403
        else:
            response = f"Recommendations of {sequence_id} for device {serial_number} deleted."
            return_code = 200

    return response, return_code, cor_id
