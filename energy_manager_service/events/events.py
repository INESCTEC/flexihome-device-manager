from marshmallow import Schema, fields


UserEnergyManagerActivationNotificationType = "UserEnergyManagerActivationNotification"
ShiftRecommendationNotificationType = "ShiftRecommendationNotification"


class UserShiftNotificationSchema(Schema):
    user_id = fields.String(required=True)
    serial_number = fields.String(required=True)
    new_start_time = fields.String(required=True)  # ISO formatted string
    language = fields.String(required=False, validate=lambda value: value in {'PT', 'EN'}, dump_default='EN')
    
    
class ShiftRecommendationNotificationSchema(Schema):
    user_id = fields.String(required=True)
    serial_number = fields.String(required=True)
    language = fields.String(required=False, validate=lambda value: value in {'PT', 'EN'}, dump_default='EN')
