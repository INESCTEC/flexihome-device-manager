from datetime import datetime, timezone

from energy_manager_service import Config
from energy_manager_service.utils.date.datetime import datetime_to_index


WINDOW_NUM    = int(60 / Config.DELIVERY_TIME)


def data_to_array(list_values, attribute_name, timestamp_name) -> []:
    """
    :return: array of data related to dt
    """
    list_timestamp = [datetime.strptime(value_[timestamp_name], Config.TIMESTAMP_FORMAT) for value_ in list_values]
    first_date = min(list_timestamp)
    first_date = first_date.replace(tzinfo=timezone.utc)
    
    data_dict = {}
    for value_ in list_values:
        idx_ = datetime_to_index(first_date, value_[timestamp_name])
        data_dict[idx_] = value_[attribute_name]
    data_dict = {idx_: data_dict[idx_] for idx_ in data_dict if idx_ < Config.PERIODS}

    data_array = [0] * Config.PERIODS
    if (len(data_dict) == Config.PERIODS):
        for dt in range(Config.PERIODS):
            data_array[dt] = data_dict[dt]
    elif (len(data_dict) == int(24)):
        for dt in range(0, Config.PERIODS, WINDOW_NUM):
            data_array[dt : dt + WINDOW_NUM] = [data_dict[dt]] * WINDOW_NUM
    else:
        raise Exception("data_to_array: inconsistent array length")

    return data_array