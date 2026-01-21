from datetime import datetime
from typing import Any

from energy_manager_service import logger, Config
from energy_manager_service.utils.date.datetime import datetime_to_index, update_format_datetime


class CycleModel:
    
    def __init__(self, manufacturer_window, cycle, start_date, serial_number, cor_id):
        
        self.manufacturer_window = manufacturer_window
        self.start_date = start_date
        self.x_correlation_id = cor_id
        
        self.serial_number = serial_number
        self.sequence_id = cycle["sequence_id"]
        
        self.window_limits = None
        self.baseline_schedule    = None
        self.consumption_expected = None
        
        self.scheduled_start_idx = None
        self.earliest_start_time = None
        self.latest_end_time = None
        self.scheduled_start_time = None
        self.expected_end_time = None
        self.duration = None
        
        # Run cycle model logic
        self.window_limits = self.__window_limits(cycle)
        
        duration_list, consumption_used = self.__power_profile_to_model_vars(cycle)
        
        self.consumption_expected = self.__expected_consumption_to_model_var(duration_list, consumption_used)


    def __window_limits(self, cycle):
        
        # NOTE: Quando não há manufacturer window há variáveis da classe que não são definidas. É suposto?
        # O que acontece quando são chamadas nos outros métodos?
        # Testar sem manufacturer window.
        if self.manufacturer_window:
            str_earliest_start_time  = update_format_datetime(cycle["earliest_start_time"])
            str_latest_end_time      = update_format_datetime(cycle["latest_end_time"])
            str_scheduled_start_time = update_format_datetime(cycle["scheduled_start_time"])
            str_expected_end_time    = update_format_datetime(cycle["expected_end_time"])

            idx_earliest_start_time = datetime_to_index(self.start_date, str_earliest_start_time)
            idx_latest_start_time   = datetime_to_index(self.start_date, str_latest_end_time)
            self.scheduled_start_idx= datetime_to_index(self.start_date, str_scheduled_start_time)
            idx_expected_end_time   = datetime_to_index(self.start_date, str_expected_end_time)

            self.earliest_start_time  = datetime.strptime(str_earliest_start_time, Config.TIMESTAMP_FORMAT)
            self.latest_end_time      = datetime.strptime(str_latest_end_time, Config.TIMESTAMP_FORMAT)
            self.scheduled_start_time = datetime.strptime(str_scheduled_start_time, Config.TIMESTAMP_FORMAT) 
            self.expected_end_time    = datetime.strptime(str_expected_end_time, Config.TIMESTAMP_FORMAT)
            self.duration = self.expected_end_time.timestamp() - self.scheduled_start_time.timestamp()

            if((idx_latest_start_time - idx_earliest_start_time) < (idx_expected_end_time - self.scheduled_start_idx)):
                log_message = 'The manufacturer latest_start_time condition is unfeasiable. The manufacturer-window parameter must be equal to False.'
                logger.warning(log_message, extra=self.x_correlation_id)
        else:
            idx_earliest_start_time = 0
            idx_latest_start_time   = Config.PERIODS-1
            
            
        return [idx_earliest_start_time, idx_latest_start_time]
            
            
    def __power_profile_to_model_vars(self, cycle):
        duration_list = []
        consumption_used = []
        for slot in cycle["power_profile"]: 
            duration_list.append(slot["duration"])

            if ('expected_power' in [subcls for subcls in slot.keys()]):
                expected_power = slot["expected_power"] * pow(10,-3) if str(slot["power_units"]).lower() == 'w' else slot["expected_power"]
            else:
                expected_power = slot["max_power"] * pow(10,-3) if str(slot["power_units"]).lower() == 'w' else slot["max_power"]
            consumption_used.append(expected_power/ int(60 / Config.DELIVERY_TIME))
            
            
        return duration_list, consumption_used
            
            
    def __expected_consumption_to_model_var(self, duration_list, consumption_used):
        consumption_expected = []
        
        consumption_slot_len = round(sum(duration_list) / Config.DELIVERY_TIME)
        if (0 <= (sum(duration_list) % Config.DELIVERY_TIME) <= Config.DELIVERY_TIME/2 or 
        (sum(duration_list) % Config.DELIVERY_TIME) > (Config.DELIVERY_TIME - Config.SLOT_MIN)): 
            consumption_slot_len += 1
        consumption_slot = []
        for idx in range(len(consumption_used)): 
            num_slots = round(duration_list[idx] / Config.SLOT_MIN)
            if (0 < (duration_list[idx] % Config.SLOT_MIN) <= Config.SLOT_MIN/2): 
                num_slots += 1
            consumption_slot.extend([consumption_used[idx]] * num_slots) # convert power to energy
        while (len(consumption_slot) < (consumption_slot_len * int(Config.DELIVERY_TIME/Config.SLOT_MIN))):
            consumption_slot.append(0)

        for idx in range(0, len(consumption_slot), int(Config.DELIVERY_TIME/Config.SLOT_MIN)): 
            max_p = max(consumption_slot[idx:idx+int(Config.DELIVERY_TIME/Config.SLOT_MIN)])
            if (max_p != 0):
                consumption_expected.append(max_p)
            else:
                max_p = max(consumption_slot[idx-1:idx+int(Config.DELIVERY_TIME/Config.SLOT_MIN)])
                consumption_expected.append(max_p)


        return consumption_expected
    

    def __repr__(self):
        return (
            f"""
            CycleModel(manufacturer_window={self.manufacturer_window}, 
            cycle sequence id={self.sequence_id}, 
            cycle appliance serial number={self.serial_number} 
            start_date={self.start_date})
            """
        )
