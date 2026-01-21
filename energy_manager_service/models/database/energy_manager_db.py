# coding: utf-8 
# Version: 1.1
#==============================================================================
#   Interconnect project - Energy Manager Service
#   Developer: Igor Rezende igorezc@gmail.com
#   Date: Sept 2022
#==============================================================================

from sqlalchemy import String, DateTime, Boolean, Float

from energy_manager_service import db


class DBAvailableFlexbility(db.Model):
    __tablename__ = "flexibility_available"
    __bind_key__ = "energy_manager"

    flex_id             = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(String(32), nullable=False)
    meter_id            = db.Column(String(32), nullable=False)
    request_datetime    = db.Column(DateTime, nullable=False)

    accepted_by_grid    = db.Column(Boolean, nullable=False)
    baseline_call_ok    = db.Column(Boolean, nullable=False, default=False)
    flex_up_call_ok     = db.Column(Boolean, nullable=False, default=False)
    flex_down_call_ok   = db.Column(Boolean, nullable=False, default=False)
    
    baseline_zeros      = db.Column(Boolean, nullable=False)
    flex_up_zeros       = db.Column(Boolean, nullable=False)

    vectors             = db.relationship('DBFlexibilityVectors', backref='DBAvailableFlexbility', cascade="all,delete")
    
    
    def __repr__(self):
        return "<DBAvailableFlexbility(flex_id={0}, user_id={1}, meter_id={2}, " \
            "request_datetime={3}, accepted_by_grid={4}," \
            "baseline_call_ok={5}, flex_up_call_ok={6}, flex_down_call_ok={7}, " \
            "baseline_zeros={8}, flex_up_zeros={9})>".format(
            self.flex_id,
            self.user_id, 
            self.meter_id,
            self.request_datetime,
            self.accepted_by_grid,
            self.baseline_call_ok,
            self.flex_up_call_ok,
            self.flex_down_call_ok,
            self.baseline_zeros,
            self.flex_up_zeros
        )
    

class DBFlexibilityVectors(db.Model):
    __tablename__ = "flexibility_vectors"
    __bind_key__ = "energy_manager"
    
    id                  = db.Column(db.Integer, primary_key=True)
    timestamp           = db.Column('timestamp', DateTime, nullable=False)
    baseline            = db.Column('baseline_value', Float(8), nullable=False)
    flex_up             = db.Column('flex_up_value', Float(8), nullable=False)
    flex_down           = db.Column('flex_down_value', Float(8), nullable=False)
    
    flex_id             = db.Column(db.Integer, db.ForeignKey('flexibility_available.flex_id', ondelete="CASCADE"))
    
    
    def __repr__(self):
        return "<DBFlexibilityVectors(id={0}, timestamp={1}, baseline={2}, flex_up={3}, flex_down={4})>".format(
            self.id,
            self.timestamp, 
            self.baseline,
            self.flex_up,
            self.flex_down
        )
    
    
class DBOptimizedCycles(db.Model):
    __tablename__ = "optimized_cycles"
    __bind_key__ = "energy_manager"
    
    id                      = db.Column(db.Integer, primary_key=True)
    sequence_id             = db.Column(String(128), nullable=False)
    serial_number           = db.Column(String(128), nullable=False)
    current_start_time      = db.Column(DateTime, nullable=False)
    optimized_start_time    = db.Column(DateTime, nullable=False)
    optimized_end_time      = db.Column(DateTime, nullable=False)
    auto_management         = db.Column(Boolean, nullable=False)
    flex_type               = db.Column(String(32), nullable=False)  # Baseline / Down / Up
    accepted_by_user        = db.Column(Boolean, nullable=False)
    notification_sent       = db.Column(Boolean, nullable=False, default=False)

    delay_call_ok           = db.Column(Boolean, nullable=True)
    delay_call_description  = db.Column(String(256), nullable=True)
    cycle_cancelled_before_activation = db.Column(Boolean, nullable=False, default=False)
    
    flex_id                 = db.Column(db.Integer, db.ForeignKey('flexibility_available.flex_id', ondelete="CASCADE"))
    
    
    def __repr__(self):
        return "<DBOptimizedCycles(id={0}, sequence_id={1}, serial_number={2}, " \
            "optimized_start_time={3}, optimized_end_time={4}, flex_type={5}, " \
            "accepted_by_user={6}, notification_sent={7}, delay_call_ok={8}, " \
            "delay_call_description={9}, cycle_cancelled_before_activation={10})>".format(
            self.id,
            self.sequence_id, 
            self.serial_number,
            self.optimized_start_time,
            self.optimized_end_time,
            self.flex_type,
            self.accepted_by_user,
            self.notification_sent,
            self.delay_call_ok,
            self.delay_call_description,
            self.cycle_cancelled_before_activation
        )
    

db.create_all(bind=['energy_manager'])
