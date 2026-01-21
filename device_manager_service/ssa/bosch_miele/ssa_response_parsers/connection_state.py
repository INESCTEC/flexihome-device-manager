from datetime import datetime
import pytz

from device_manager_service import generalLogger, db
from device_manager_service.models.db_models import DBShiftableMachine


def bindings_to_json(bindings):

    connection_state = bindings[0]['deviceConnectionState'].split('#')[1].replace(">", "").lower()
    if connection_state == 'connected':
        connection_state = True
    else:
        connection_state = False

    # What was posted to the KI (parsed from the "post" request bindings)
    parsed_parameters = {
        'device_connection_state': connection_state,
        'connection': bindings[0]['connection'],
        'device': bindings[0]['device'],
        'device_id': bindings[0]['deviceId'].replace("\"", ""),
        # 2023-11-22T18:41:36.000059+01:00
        'timestamp': datetime.strptime(bindings[0]['timestamp'].replace("\"", ""), '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(pytz.utc)
        }

    return parsed_parameters


def process_connection_state(session, bindings):
    parsed_parameters = bindings_to_json(bindings)
    generalLogger.debug(parsed_parameters)

    generalLogger.info(
        f"Device {parsed_parameters['device_id']} " \
        f"changed connection state to {parsed_parameters['device_connection_state']} " \
        f"at {parsed_parameters['timestamp']}"
    )

    # Query device from db
    device_in_db = session.query(DBShiftableMachine).filter_by(serial_number=parsed_parameters['device_id']).first()
    if device_in_db is not None:
        # Update device connection state
        db_connection_timestamp = pytz.utc.localize(device_in_db.connection_state_timestamp)
        if parsed_parameters['timestamp'] > db_connection_timestamp:
            device_in_db.connection_state = parsed_parameters['device_connection_state']
            device_in_db.connection_state_timestamp = parsed_parameters['timestamp']
            session.commit()
        else:
            generalLogger.warning(f"Not updating device {parsed_parameters['device_id']} timestamp, because current saved timestamp {db_connection_timestamp} is more recent than new timestamp {parsed_parameters['timestamp']}")
        
        generalLogger.info(f"Device {parsed_parameters['device_id']} connection state updated to {parsed_parameters['device_connection_state']} in DB")
