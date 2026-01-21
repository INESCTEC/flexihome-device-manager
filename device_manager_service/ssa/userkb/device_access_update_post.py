import uuid
from datetime import datetime, timezone

from device_manager_service import generalLogger, db, userkb_ssa
# from device_manager_service.ssa.ssa_classes.userkb_ssa import UserkbSSA
from device_manager_service.ssa.ssa_config.userkb_config import UserkbConfig
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig

from device_manager_service.utils.database.db_interactions import commit_db_changes

from device_manager_service.models.db_models import DBShiftableMachine


# Specific Service Adapter logic #

def device_access_update_post(serial_number: str, device_ssa: str, status: bool):
    generalLogger.info("# DEVICE ACCESS UPDATE POST #\n")


    kbs_to_give_access = [
        f"{BSHConfig.INESCTEC_BSH_SERVICE_PRIMARY_URL}/adapter/{BSHConfig.KB_ASSET_ID}",
        f"{BSHConfig.INESCTEC_BSH_SERVICE_PRIMARY_URL}/adapter/{BSHConfig.KB_REACT_ASSET_ID}"
    ]
    
    for kb in kbs_to_give_access:
        bindings = [{
            "kb": kb, 
            "deviceSsa": f"{device_ssa}",
            "event": f"http://pt-pilot.example.org/events/{uuid.uuid4()}",
            "deviceId": f"{serial_number}",
            "device": f"<http://example.org/spine-ssa/devices/{serial_number}>",
            "status": f"{str(status).lower()}",
            "timestamp": f"{datetime.now(timezone.utc).isoformat()}"
        }]


        try:
            response, status_code = userkb_ssa.ask_or_post(
                bindings=bindings,
                ki_id=userkb_ssa.userkb_device_access_ki,
                response_wait_timeout_seconds=UserkbConfig.SSA_TIMEOUT_SECONDS,
                self_heal=True,
                delete_kb_when_self_heal=True,
                self_heal_tries=2
            )
        except Exception as e:
            generalLogger.error(f"Error in SSA post request: {repr(e)}")
            
            return "Error in SSA ask/post request", 500
        
        generalLogger.info(f"SSA post response status code: {status_code}")
        
        if "exchangeInfo" in response.keys():
            if len(response["exchangeInfo"][0]["resultBindingSet"]) != 0:
                try:
                    message = response["exchangeInfo"][0]["resultBindingSet"][0]["bodyText"].replace('"', '')
                    status_code = int(response["exchangeInfo"][0]["resultBindingSet"][0]["statusCodeValue"].replace('"', ''))
                    generalLogger.info(f"Device access update interaction response: {message}")
                    
                except KeyError as e:
                    generalLogger.error(f"Error processing device access update interaction: {repr(e)}")
                    message = f"Error processing device {serial_number} access update to {status}"
                    status_code = 400
            
            else:
                
                try:
                    device_in_db = DBShiftableMachine.query.filter_by(serial_number=serial_number).first()            
                    device_in_db.allow_hems = status
                    device_in_db.automatic_management = status
                    db_error_msg = f"Database failed to COMMIT to database\n"
                    _ = commit_db_changes(db.session, db_error_msg)
                    
                except Exception as e:
                    generalLogger.error(f"Error updating device access in DB: {repr(e)}")
                    message = f"Error updating device {serial_number} access to {status} in DB"
                    status_code = 400
                
                else:
                    message = f"Successfully update device {serial_number} access to {status}"
                    status_code = 200

            generalLogger.info(f'Device access update interaction for kb: {kb}... DONE\n')

            if status_code != 200:
                break
        else:
            generalLogger.error("SSA call failed with empty exchangeInfo. It is likely a GP mismatch. Check your GPs.")
            message = f"Empty ExchangeInfo. Failed to update device {serial_number} access to {status}"
            status_code = 400
            break
    
    
    return message, status_code
