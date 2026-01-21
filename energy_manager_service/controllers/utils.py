from energy_manager_service import logger

#==============================================================================
def logErrorResponse(error, endText, response, cor_id):
    logger.error(error, extra=cor_id)
    logResponse(endText, response, cor_id)
#==============================================================================
def logResponse(endText, response, cor_id):
    logger.info(f"{endText}\n", extra=cor_id)
    if response is not None:
        logger.debug("Sending the following response: ", extra=cor_id)
        logger.debug(f"{response}\n", extra=cor_id)
#==============================================================================
