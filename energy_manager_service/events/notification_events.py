import asyncio, json, os, uuid

from aiokafka import AIOKafkaProducer
from random import randint

from energy_manager_service import generalLogger

from energy_manager_service.events.events import (
    UserShiftNotificationSchema,
    ShiftRecommendationNotificationSchema,
    UserEnergyManagerActivationNotificationType,
    ShiftRecommendationNotificationType
)

# ENV VARIABLES
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', "hems.notifications")
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# GLOBAL VARIABLES
loop = asyncio.get_event_loop()

################################################################################################
#  NOTIFICATION EVENTS FUNCS
################################################################################################
async def send_shift_notification(serial_number, new_start_time, user_id, language):
    generalLogger.info(f"Sending new shift notification to user {user_id}")
    
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    
    # get cluster layout and initial topic/partition leadership information
    await producer.start()
    
    # A hora de início do programa da máquina {serial_number} foi alterada para as {new_start_time_formatted}
    energy_manager_activation_payload = {
        "user_id": user_id,
        "serial_number": serial_number,
        "new_start_time": new_start_time,
        "language": language
    }
    user_notification_schema = UserShiftNotificationSchema()
    payload = user_notification_schema.dump(energy_manager_activation_payload)
    generalLogger.debug(payload)
    
    try:
        # produce message
        msg_id = f'{randint(1, 10000)}'
        value = {
            'message_id': msg_id,
            'payload': payload,
            'eventId': str(uuid.uuid4()),
            'eventType': UserEnergyManagerActivationNotificationType
        }
        
        generalLogger.info(f'Sending message with value: {value}')
        value_json = json.dumps(value).encode('utf-8')
        
        await producer.send_and_wait(
            KAFKA_TOPIC, 
            value_json
            )
    
    finally:
        # wait for all pending messages to be delivered or expire.
        await producer.stop()
        

async def send_shift_recommendation_notification(serial_number, user_id, language):
    generalLogger.info(f"Sending shift recommendation notification to user {user_id}")
    
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    
    # get cluster layout and initial topic/partition leadership information
    await producer.start()
    
    
    energy_manager_activation_payload = {
        "user_id": user_id,
        "serial_number": serial_number,
        "language": language
    }
    shift_recommendation_notification_schema = ShiftRecommendationNotificationSchema()
    payload = shift_recommendation_notification_schema.dump(energy_manager_activation_payload)
    generalLogger.debug(payload)
    
    try:
        # produce message
        msg_id = f'{randint(1, 10000)}'
        value = {
            'message_id': msg_id,
            'payload': payload,
            'eventId': str(uuid.uuid4()),
            'eventType': ShiftRecommendationNotificationType
        }
        
        generalLogger.info(f'Sending message with value: {value}')
        value_json = json.dumps(value).encode('utf-8')
        
        await producer.send_and_wait(
            KAFKA_TOPIC,
            value_json
            )
    
    finally:
        # wait for all pending messages to be delivered or expire.
        await producer.stop()
