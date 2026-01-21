from energy_manager_service import auth, logger

from energy_manager_service.models.error import Error

from energy_manager_service.controllers.utils import logErrorResponse


def verify_hems_auth(request_headers, user_ids, end_text, cor_id, internal_request=False):
    auth_response, auth_code = auth.verify_basic_authorization(request_headers)
    
    response = None
    response_code = 200

    if auth_code != 200:

        logger.error(auth_response, extra=cor_id)
        
        msg = "Invalid credentials. Check logger for more info."
        response = Error(msg)
        response_code = auth_code

        logErrorResponse(msg, end_text, response, cor_id)

    elif auth_code == 200 and auth_response is not None:

        logger.info(
            f"User {auth_response} accessing from API Gateway...",
            extra=cor_id
        )

        if internal_request:
            msg = "Request not allowed through API Gateway." # 403
        
            response = Error(msg)
            response_code = 403

            logErrorResponse(msg, end_text, response, cor_id)

        elif user_ids:
            if len(user_ids) > 1:
                logger.error(
                    f"User {auth_response} tried to access other users accounts.\n",
                    extra=cor_id
                )
                msg = "Unauthorized action!"
                response = Error(msg)
                response_code = 403

                logErrorResponse(msg, end_text, response, cor_id)

            if user_ids[0] != auth_response:
                logger.error(
                    f"User {auth_response} trying to access different user devices ({user_ids[0]})",
                    extra=cor_id
                )

                msg = "Unauthorized action!"
                response = Error(msg)
                response_code = 403

                logErrorResponse(msg, end_text, response, cor_id)

        user_ids = [auth_response]

        logger.info(f"Listing devices from user {auth_response}\n", extra=cor_id)

    else:
        logger.info(
            f"Request is made by an internal service. Proceeding...",
            extra=cor_id
        )
    

    return response, response_code, user_ids