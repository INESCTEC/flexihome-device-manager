from datetime import datetime, timedelta, timezone

from energy_manager_service.config import Config


def datetime_to_index(start_time, timestamp_str):
    timestamp_ = datetime.strptime(timestamp_str, Config.TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    delivery_time_idx = int((timestamp_.timestamp() - start_time.timestamp())/60 / Config.DELIVERY_TIME)
    # if (delivery_time_idx >= PERIODS):
    #     delivery_time_idx = PERIODS - 1
    #==============================================================================
    return delivery_time_idx
#==============================================================================
def update_format_datetime(timestamp_str):
    new_timestamp_str = timestamp_str
    if (timestamp_str.find('.') >= 0):
        new_timestamp_str = timestamp_str.replace(timestamp_str[timestamp_str.find('.'):timestamp_str.find('Z')], "")
    #==============================================================================
    return new_timestamp_str
#==============================================================================
def index_to_datetime(start_time, delivery_time_idx):
    timestamp_ = start_time + timedelta(minutes=(delivery_time_idx * Config.DELIVERY_TIME)) 
    timestamp_ = timestamp_.replace(tzinfo=timezone.utc)
    #==============================================================================
    return timestamp_