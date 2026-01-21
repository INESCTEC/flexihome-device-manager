# import psycopg2

from device_manager_service import db, logger, generalLogger


def add_row_to_table(session, db_row, error_msg, cor_id = None):
    code = 200

    try:
        session.add(db_row)
        session.flush()

    except Exception as e:
        session.rollback()
        
        if cor_id is None:
            generalLogger.error(repr(e))
            generalLogger.error(error_msg)
        else:
            logger.error(repr(e), extra=cor_id)
            logger.error(error_msg, extra=cor_id)

        code = 500
        
        generalLogger.debug("Closing DB session")
        session.close()
            
    # finally:
    #     generalLogger.debug("Closing DB session")
    #     db.session.close()

    
    return code


def commit_db_changes(session, error_msg, cor_id = None):
    code = 200

    try:
        session.commit()
    
    except Exception as e:
        session.rollback()
        
        if cor_id is None:
            generalLogger.error(repr(e))
            generalLogger.error(error_msg)
        else:
            logger.error(repr(e), extra=cor_id)
            logger.error(error_msg, extra=cor_id)

        code = 500

    finally:
        generalLogger.debug("Closing DB session")
        session.close()
        
    
    return code


def delete(session, object_to_delete, error_msg, cor_id = None):
    code = 200

    try:
        session.delete(object_to_delete)
    
    except Exception as e:
        session.rollback()
        
        if cor_id is None:
            generalLogger.error(repr(e))
            generalLogger.error(error_msg)
        else:
            logger.error(repr(e), extra=cor_id)
            logger.error(error_msg, extra=cor_id)

        code = 500
        
        generalLogger.debug("Closing DB session")
        session.close()

    # finally:
    #     generalLogger.debug("Closing DB session")
    #     session.close()
        
    
    return code


def add_and_commit(session, db_row, error_msg, cor_id = None):
    
    code = add_row_to_table(session, db_row, error_msg, cor_id)
    if code == 200:
        code = commit_db_changes(session, error_msg, cor_id)
    
    return code


def delete_and_commit(session, object_to_delete, error_msg, cor_id = None):
    
    code = delete(session, object_to_delete, error_msg, cor_id)
    if code == 200:
        code = commit_db_changes(session, error_msg, cor_id)
    
    return code


# def ssa_add_row_to_table(db_row, error_msg):
#     code = 200
    
#     try:
#         db.session.add(db_row)
#         db.session.flush()

#     except Exception as e:
#         db.session.rollback()
#         generalLogger.error(repr(e))
#         generalLogger.error(error_msg)

#         code = 500
#         # raise psycopg2.DatabaseError("Failed to add row to the database")

#     finally:
#         generalLogger.debug("Closing DB session")
#         db.session.close()


#     return code


# def ssa_commit_db_changes(error_msg):
#     code = 200
    
#     try:
#         db.session.commit()
    
#     except Exception as e:
#         db.session.rollback()
#         generalLogger.error(repr(e))
#         generalLogger.error(error_msg)

#         code = 500
#         # raise psycopg2.DatabaseError("Failed to commit changes to the database")

#     finally:
#         generalLogger.debug("Closing DB session")
#         db.session.close()
    
    
#     return code
