from device_manager_service import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey, Column, Integer
from datetime import datetime, timedelta, timezone
import jwt
from device_manager_service import Config
import string
import random
import uuid


# TODO: Only create account manager tables if TESTING flag is true


class DBShiftableMachine(db.Model):
    __tablename__ = "db_shiftable_machine"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)
    brand = db.Column(db.String(64), nullable=False)
    serial_number = db.Column(db.String(64), nullable=False)  # serial_number = deviceAddress
    allow_hems = db.Column(db.Boolean, nullable=False, default=True)
    automatic_management = db.Column(db.Boolean, nullable=False, default=True)
    device_ssa = db.Column(db.String(128), nullable=True)
    connection_state = db.Column(db.Boolean, nullable=True, default=True)
    connection_state_timestamp = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    current_cycle_id = Column(
        Integer, ForeignKey("db_shiftable_cycle.id", ondelete="CASCADE"), nullable=True
    )
    # One-To-One relationship for convinience (one machine has one current cycle)
    current_cycle = relationship(
        "DBShiftableCycle",
        backref=backref("shiftable_machine", uselist=False),
        foreign_keys=[current_cycle_id]
    )

    # Many-To-One relationship (one machine has multiple cycles)
    washing_cycles = relationship(
        "DBShiftableCycle",
        cascade="all,delete-orphan",
        foreign_keys="DBShiftableCycle.shiftable_machine_id"
    )

    not_disturb = relationship(
        "DBNotDisturb",
        cascade="all, delete-orphan",
    )


    def __repr__(self):
        return f"DBShiftableMachine(" \
            f"id={self.id}, name={self.name}, device_type='{self.device_type}'," \
            f"brand={self.brand}, serial_number={self.serial_number}, current_cycle_id={self.current_cycle_id}, " \
            f"allow_hems={self.allow_hems}, user_id={self.user_id}, device_ssa={self.device_ssa}, " \
            f"washing_cycles={len(self.washing_cycles)}, not_disturb={self.not_disturb})"


class DBShiftableCycle(db.Model):
    __tablename__ = "db_shiftable_cycle"
    id = db.Column(db.Integer, primary_key=True)
    sequence_id = db.Column(db.String(128), nullable=False, unique=False)
    earliest_start_time = db.Column(db.DateTime, nullable=False)
    latest_end_time = db.Column(db.DateTime, nullable=False)
    scheduled_start_time = db.Column(db.DateTime, nullable=False)
    expected_end_time = db.Column(db.DateTime, nullable=False)
    program = db.Column(db.String(64), nullable=False)
    is_optimized = db.Column(db.Boolean, nullable=False)

    power_profile = relationship(
        "DBShiftablePowerProfile",
        cascade="all,delete",
        backref="DBShiftableCycle"
    )

    shiftable_machine_id = Column(
        Integer, ForeignKey("db_shiftable_machine.id", ondelete="CASCADE")
    )

    def __repr__(self):
        return f"DBShiftableCycle(" \
            f"id={self.id}, sequence_id={self.sequence_id}," \
            f"earliest_start_time={self.earliest_start_time}" \
            f"latest_end_time={self.latest_end_time}" \
            f"scheduled_start_time={self.scheduled_start_time}," \
            f"expected_end_time='{self.expected_end_time}', program={self.program}," \
            f"is_optimized={self.is_optimized}, power_profile_slots={len(self.power_profile)}, " \
            f"shiftable_machine_id={self.shiftable_machine_id})"


# Old cycles before being delayed. Only kept variables that could change
# Can be used to fetch historic of delays of a cycle
class DBShiftableCycleOld(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sequence_id = db.Column(db.String(128), nullable=False, unique=False)
    earliest_start_time = db.Column(db.DateTime, nullable=False)
    latest_end_time = db.Column(db.DateTime, nullable=False)
    scheduled_start_time = db.Column(db.DateTime, nullable=False)
    expected_end_time = db.Column(db.DateTime, nullable=False)

    cycle_ref = db.Column(
        db.Integer, ForeignKey("db_shiftable_cycle.id", ondelete="CASCADE")
    )

    def __repr__(self):
        return f"DBShiftableCycle(" \
            f"id={self.id}, sequence_id={self.sequence_id}," \
            f"earliest_start_time={self.earliest_start_time}" \
            f"latest_end_time={self.latest_end_time}" \
            f"scheduled_start_time={self.scheduled_start_time}," \
            f"expected_end_time='{self.expected_end_time}', cycle_ref={self.cycle_ref})" \
            f"creation_timestamp={self.creation_timestamp}"


class DBShiftablePowerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot = db.Column(db.Integer, nullable=False)
    max_power = db.Column(db.Float, nullable=False)
    min_power = db.Column(db.Float, nullable=True)
    expected_power = db.Column(db.Float, nullable=True)
    power_units = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    duration_units = db.Column(db.String(64), nullable=False)

    cycle_ref = db.Column(
        db.Integer, ForeignKey("db_shiftable_cycle.id", ondelete="CASCADE")
    )

    def __repr__(self):
        return f"DBShiftablePowerProfile(" \
            f"id={self.id}, slot={self.slot}, max_power={self.max_power}," \
            f"min_power={self.min_power}, expected_power={self.expected_power}," \
            f"power_units='{self.power_units}', duration={self.duration}," \
            f"duration_units='{self.duration}', cycle_ref={self.cycle_ref})"


class DBNotDisturb(db.Model):
    __tablename__ = "db_not_disturbs"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.ForeignKey("db_shiftable_machine.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    not_disturb = db.relationship(
        "DBShiftableMachine", back_populates="not_disturb", lazy="joined"
    )
    day_of_week = db.Column(db.String(32), nullable=False)
    start_timestamp = db.Column(db.DateTime, nullable=False)
    end_timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"DBNotDisturb('{self.day_of_week}', '{self.start_timestamp}', '{self.end_timestamp}')"


class DBProcessedEvent(db.Model):
    __tablename__ = 'processed_events'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(255), nullable=False)  # Topic name
    event_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)

    def __repr__(self):
        return f"DBProcessedEvent('{self.event_type}', '{self.event_id}')"


class DBDongles(db.Model):
    __tablename__ = "db_dongles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), unique=True, index=True, nullable=False)
    api_key = db.Column(db.String(32), nullable=True)  # Dongle API Key

    def __repr__(self):
        return f"DBDongles('{self.event_type}', '{self.event_id}')"

# Processed Event table #
# class DBProcessedEvent(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     eventType = db.Column(db.String(255), nullable=False)  # Topic name
#     eventId = db.Column(UUID(as_uuid=True), nullable=False, index=True)

#     def __repr__(self):
#         return f"DBProcessedEvent('{self.eventType}', '{self.eventId}')"

# -------------- ACCOUNT MANAGER DATABASE FOR TESTING -------------- #


def id_generator(
    size=Config.USER_ID_SIZE, chars=string.ascii_lowercase + string.digits
):
    return "".join(random.choice(chars) for _ in range(size))


class DBUser(db.Model):
    __tablename__ = "users"
    __bind_key__ = "account_manager"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), unique=True, index=True,nullable=False, default=id_generator)
    meter_id = db.Column(db.String(32), unique=True, index=True)

    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=False)
    is_google_account = db.Column(db.Boolean, nullable=False, default=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    api_key = db.Column(db.String(32), nullable=True)  # Dongle API Key
    wp_token = db.Column(db.String(500), nullable=True)  # WP account token
    expo_token = db.Column(db.String(128), nullable=True)  # Expo notification token
 
    created_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    settings = db.relationship("DBUserSettings", back_populates="user", lazy="joined", uselist=False)

    def __repr__(self):
        return (
            f"DBUser('{self.user_id}', '{self.first_name}', " \
            f"'{self.last_name}', '{self.email}', '{self.password}', '{self.is_active}', " \
            f"'{self.deleted}', '{self.meter_id}', '{self.api_key}', " \
            f"'{self.expo_token}', '{self.wp_token}', '{self.is_google_account}', " \
            f"'{self.settings}', '{self.created_timestamp}', '{self.modified_timestamp}')"
        )

    def encode_auth_token(self):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_EXPIRATION_TIME_SECONDS),
                'iat': datetime.now(timezone.utc),
                'sub': self.user_id,
                'email': self.email,
                'meter_id': self.meter_id
            }
            return jwt.encode(
                payload,
                Config.JWT_SIGN_KEY,
                algorithm=Config.JWT_SIGN_ALGORITHM
            )
        except Exception as e:
            print(e)
            return None

    @ staticmethod
    def decode_auth_token(auth_token):
        """
        Validates the auth token
        :param auth_token:
        :return: string
        """
        try:
            payload = jwt.decode(auth_token, Config.JWT_SIGN_KEY, algorithms=[
                Config.JWT_SIGN_ALGORITHM])
            # is_blacklisted_token = TokenBlacklist.check_blacklist(auth_token)
            # if is_blacklisted_token:
            #     raise Exception('Token blacklisted. Please log in again.')
            # else:
            #     return payload['sub']
            return payload['sub']
        except Exception as e:
            raise


class DBUserSettings(db.Model):
    __tablename__ = "user_settings"
    __bind_key__ = "account_manager"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("users.user_id"), index=True, nullable=False)

    country = db.Column(db.String(32), nullable=True)
    postal_code = db.Column(db.String(32), nullable=True)

    schedule_type = db.Column(db.String(32), nullable=True, default=Config.DEFAULT_SCHEDULE_TYPE)
    tarif_type = db.Column(db.String(32), nullable=True)
    contracted_power = db.Column(db.String(32), nullable=True)

    global_optimizer = db.Column(db.Boolean, nullable=True, default=True)
    permissions = db.Column(db.String(32), nullable=False, default="None")

    modified_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("DBUser", back_populates="settings", lazy="joined")
    not_disturb = db.relationship("DBNotDisturbUser", lazy="joined", back_populates="settings")


    def __repr__(self):
        return (
            f"DBUserSettings('{self.country}', '{self.postal_code}', " \
            f"'{self.schedule_type}', '{self.tarif_type}', '{self.contracted_power}', " \
            f"'{self.not_disturb}', '{self.global_optimizer}', " \
            f"'{self.permissions}', '{self.modified_timestamp}')"
        )


class DBNotDisturbUser(db.Model):
    __tablename__ = 'not_disturbs'
    __bind_key__ = 'account_manager'

    id = db.Column(db.Integer, primary_key=True)
    settings_id = db.Column(db.ForeignKey("user_settings.id"),
                            index=True, nullable=False)
    settings = db.relationship(
        "DBUserSettings", back_populates="not_disturb", lazy="joined")
    day_of_week = db.Column(db.String(32), nullable=False)
    start_timestamp = db.Column(db.String(32), nullable=False)
    end_timestamp = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return f"DBNotDisturb('{self.day_of_week}', '{self.start_timestamp}', '{self.end_timestamp}')"


class DBConfirmationToken(db.Model):
    __tablename__ = "confirmation_tokens"
    __bind_key__ = "account_manager"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), index=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expiration_timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"DBConfirmationToken('{self.user_id}', '{self.token}', '{self.expiration_timestamp}')"


class DBForgotPasswordToken(db.Model):
    __tablename__ = "forgot_password_tokens"
    __bind_key__ = "account_manager"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), index=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expiration_timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"DBForgotPasswordToken('{self.user_id}', '{self.token}', '{self.expiration_timestamp}')"

class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'
    __bind_key__ = 'jwt_token_management'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(512), index=True,
                        unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)

    def __repr__(self):
        return f"TokenBlacklist('{self.token}', '{self.timestamp}')"

class DBEvent(db.Model):
    __tablename__ = 'events'
    __bind_key__ = 'account_manager'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregatetype = db.Column(
        db.String(255), nullable=False, default=Config.KAFKA_TOPIC_SUFFIX)  # Topic name
    aggregateid = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payload = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f"DBEvent('{self.aggregatetype}', '{self.aggregateid}', '{self.type}', '{self.timestamp}', '{self.payload}')"


# class DBProcessedEvent(db.Model):
#     __tablename__ = 'processed_events'
#     __bind_key__ = 'account_manager'

#     id = db.Column(db.Integer, primary_key=True)
#     event_type = db.Column(db.String(255), nullable=False)  # Topic name
#     event_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)

#     def __repr__(self):
#         return f"DBProcessedEvent('{self.event_type}', '{self.event_id}')"


db.create_all()
