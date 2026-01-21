import traceback
from types import SimpleNamespace
from typing import List

from datetime import datetime, timedelta, timezone

from energy_manager_service import logger, Config, db
from energy_manager_service.controllers.default_data import Default_data

from energy_manager_service.models.error import Error
from energy_manager_service.models.schedule_response import ScheduleResponse

from energy_manager_service.models.cycle_model_vars import CycleModel

from energy_manager_service.models.database.energy_manager_db import DBOptimizedCycles

from energy_manager_service.utils.date.datetime import index_to_datetime
from energy_manager_service.utils.type_conversion.data_to_array import data_to_array

from energy_manager_service.clients.hems_services.account_manager import get_user 
from energy_manager_service.clients.hems_services.device_manager import (
    get_schedule_cycle_by_user,
    get_settings_by_device
)
from energy_manager_service.clients.hems_services.energy_prices import get_tarif_periods_erse
from energy_manager_service.clients.hems_services.forecast import get_forecast
from energy_manager_service.clients.hems_services.statistics_manager import get_co2_intensity_forecast

from energy_manager_service.optimizers.save_flexibility import save_available_flexibility


WINDOW_NUM = int(60 / Config.DELIVERY_TIME)


class OptimizerPipeline:
    
    def __init__(self, user_id, x_correlation_id, manufacturer_window = True) -> None:
        
        default_data_instance = Default_data()

        self.manufacturer_window    = manufacturer_window
        self.user_id                = user_id
        self.x_correlation_id       = x_correlation_id
        self.start_date             = (datetime.now() + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
        self.contracted_power_value = default_data_instance.CONTRACTED_POWER
        self.production_value_p     = default_data_instance.FORECAST_PRODUCTION
        self.consumption_value_p    = default_data_instance.FORECAST_CONSUMPTION
        self.prices_sell            = default_data_instance.PRICES_SELL
        self.prices_buy             = default_data_instance.PRICES_BUY
        
        
        self.pool_appliances        = None
        
    
    
    def inputs_call(self):
        
        
        # ----------------------- Account manager -> get user ----------------------- #
        
        user_response, status_code = get_user(self.user_id, self.x_correlation_id)
        
        if status_code >= 300:
            return Error(user_response["error"]), status_code, self.x_correlation_id
        else:
            user_response = user_response[0]

        # Contracted power
        self.contracted_power_value = float(str(user_response["contracted_power"])[0:str(user_response["contracted_power"]).find(' ')])

        # Contracted tariff
        tariff_type = user_response["tarif_type"].lower()
        if tariff_type == 'simple':
            incentive_type = 'ecologic'
        else:
            incentive_type = 'mixed'


        # --------------------------- Energy prices - Buy --------------------------- #
                
        energy_prices_response, status_code = get_tarif_periods_erse(
            self.start_date, 
            tariff_type, 
            self.x_correlation_id
        )
        if status_code >= 300:
            return Error(energy_prices_response["error"]), status_code, self.x_correlation_id
        
        # Convert tariffs in local time to utc
        utc_price_data = []
        for price_data in energy_prices_response["tariffs"]:
            
            price_data["timestamp"] = datetime.strptime(
                price_data["timestamp"], Config.TIMESTAMP_WITH_TZ_FORMAT
            ).astimezone(
                tz=timezone.utc
            ).strftime(
                Config.TIMESTAMP_FORMAT
            )
            
            utc_price_data.append(price_data)
        energy_prices_response["tariffs"] = utc_price_data
        
        # Convert energy prices to input
        try:
            self.prices_buy = data_to_array( 
                list_values = energy_prices_response["tariffs"], 
                attribute_name = 'price_type',
                timestamp_name = 'timestamp'
            )
        
        except Exception as e:
            error = {"error": f"Error: failed to convert energy prices to array {repr(e)}"}
            logger.error(error["error"], extra=self.x_correlation_id)
            
            return Error(error), 400, self.x_correlation_id
        
        
        # ------------------------------- Eco signal ------------------------------- #
        
        eco_signal_forecast_response, status_code = get_co2_intensity_forecast(
            self.start_date.date(), 
            self.x_correlation_id
        )
        if status_code >= 300:
            return Error(eco_signal_forecast_response["error"]), status_code, self.x_correlation_id
        
        
        updated_at_recently = max([datetime.strptime(data["updated_at"], Config.TIMESTAMP_FORMAT) for data in eco_signal_forecast_response])
        
        list_values = []
        for data in eco_signal_forecast_response:
            if (datetime.strptime(data["updated_at"], Config.TIMESTAMP_FORMAT) == updated_at_recently):
                list_values.append(data)
        
        try:
            self.co2_emission = data_to_array(
                list_values = list_values, 
                attribute_name = 'value',
                timestamp_name = 'datetime'
                )
        
        except Exception as e:
            error = {"error": f"Error: failed to convert eco signal values to array {repr(e)}"}
            logger.error(error["error"], extra=self.x_correlation_id)
            
            logger.warning(
                "CO2 incentive will not be considered in the optimization",
                extra=self.x_correlation_id
            )
            self.co2_emission = [0] * Config.PERIODS
        
        
        # -------------------------------- Forecast -------------------------------- #
        
        for value_type in Config.FORECAST_TYPE:
            
            forecast_value_p = [0] * Config.PERIODS
            self.installation_code = f'{self.user_id}_{value_type}'
            forecast_response, status_code = get_forecast(
                self.installation_code, 
                self.start_date, 
                self.x_correlation_id
            )
            
            # Forecast endpoint returns error code
            if status_code >= 300:
                return Error(forecast_response["error"]), status_code, self.x_correlation_id
                
            forecast_response = forecast_response["data"][0]

            try:
                forecast_value_p = data_to_array(
                    list_values = forecast_response["values"], 
                    attribute_name = 'value_p',
                    timestamp_name = 'timestamp'
                )
            
            except Exception as e:
                traceback.print_exc()
                error = {"error": f"Error: failed to convert forecast values to array {repr(e)}"}
                logger.error(error["error"], extra=self.x_correlation_id)
                
                return Error(error), 400, self.x_correlation_id
            
            
            forecast_value_p = [abs(forecast_value_p[dt] / WINDOW_NUM) * pow(10, -3) for dt in range(Config.PERIODS)] 

            if (value_type == Config.FORECAST_TYPE[0]):
                self.consumption_value_p = forecast_value_p

        self.consumption_value_p = [value_ * self.contracted_power_value for value_ in self.consumption_value_p]


        # ------------------ Device manager -> User cycles in pool ------------------ #
        
        user_schedules_response, status_code = get_schedule_cycle_by_user(
            self.user_id,
            self.start_date,
            self.start_date.replace(hour=23, minute=59, second=59),
            self.x_correlation_id
        )
        
        # Device manager request returns error code
        if status_code >= 300:
            return Error(user_schedules_response["error"]), status_code, self.x_correlation_id

        # User has no cycles in pool
        if sum(len(cycle["cycles"]) for item in user_schedules_response for cycle in item["cycles"]) == 0:
            # TODO: Make a message for when the status code is 202 accepted, should not be an error
            return Error("User has no cycles in pool"), 202, self.x_correlation_id
            
        self.pool_appliances = self.user_pool_to_model_vars(user_schedules_response[0]["cycles"])  # User's cycles

        
        # ------------------- Update weight values for scheduler ------------------- #
        
        logger.info(
            'All the necessary data to run the scheduler was collected',
            extra=self.x_correlation_id
        )
        
        
        logger.info("Updating weight values...", extra=self.x_correlation_id)
        logger.debug(self.prices_buy, extra=self.x_correlation_id)
        logger.debug(self.co2_emission, extra=self.x_correlation_id)

        # Update weight values
        if (incentive_type == "ecologic"):
            self.weight_buy  = self.co2_emission
            self.weight_sell = [int(0)] * Config.PERIODS
        elif (incentive_type == "economic"):
            self.weight_buy  = self.prices_buy
            self.weight_sell = self.prices_sell
        elif (incentive_type == "mixed"):
            self.weight_buy  = [0.5 * (value_1 + value_2) for value_1, value_2 in zip(self.prices_buy, self.co2_emission)]
            self.weight_sell = self.prices_sell


        return self, 200, self.x_correlation_id 

    
    def inputs_update(self, outputs_opt_baseline):

        #==============================================================================
        # Device manager - Update window constrains
        #-------------------------------------------------------------------------------
        for cycles_in_pool in self.pool_appliances:
            for cycle in cycles_in_pool:
                for result_cycle in outputs_opt_baseline.shiftable_cycles_result:
                    if (result_cycle.sequence_id == cycle.sequence_id):
                        cycle.baseline_schedule = result_cycle.schedule
        

        logger.info("Adding baseline values to cycle restriction windows...", extra=self.x_correlation_id)
        logger.debug(self.prices_buy, extra=self.x_correlation_id)

        #==============================================================================
        return self, 200, self.x_correlation_id
    
    def user_pool_to_model_vars(self, get_pool_per_user_resp) -> List[CycleModel]:
        
        pool_appliances = []
        for appliance in get_pool_per_user_resp:
            cycles_in_pool = []
            
            for cycle in appliance["cycles"]:
                cycle_model_vars = CycleModel(
                    self.manufacturer_window, cycle, self.start_date, appliance['serial_number'], self.x_correlation_id
                )
                
                cycles_in_pool.append(cycle_model_vars)
            
            if len(cycles_in_pool) != 0:
                pool_appliances.append(cycles_in_pool)
                
        return pool_appliances
    
    
    def outputs_cycles(self, flex_id, flex_type, shiftable_cycles_result):

        for appliance in self.pool_appliances:
            for cycle in appliance: 
                for result_cycle in shiftable_cycles_result:
                    
                    if result_cycle.sequence_id == cycle.sequence_id:
                        # Get device settings
                        device_settings_response, status_code = get_settings_by_device(
                            cycle.serial_number, 
                            self.x_correlation_id
                        )
                        
                        # Process response from settings request
                        if status_code >= 300:
                            return Error(device_settings_response["error"]), status_code, self.x_correlation_id
                        
                        cycle.auto_management = device_settings_response[0]["settings"][0]["automatic_management"]

                        # Update start_time cycle in pool class 
                        if (cycle.scheduled_start_idx != result_cycle.schedule[0]):
                            new_scheduled_start_time = index_to_datetime(self.start_date, result_cycle.schedule[0])
                            new_expected_end_time    = new_scheduled_start_time + timedelta(seconds= cycle.duration)
                            cycle.new_scheduled_start_time = new_scheduled_start_time.strftime(Config.TIMESTAMP_FORMAT)
                            cycle.new_expected_end_time    = new_expected_end_time.strftime(Config.TIMESTAMP_FORMAT)
                            
                        else:
                            cycle.new_scheduled_start_time = cycle.scheduled_start_time
                            cycle.new_expected_end_time = cycle.expected_end_time
                            
                            logger.info(
                                f'The cycle {cycle.sequence_id} start_time is preserved. The solution found did not indicate a delay.',
                                extra=self.x_correlation_id
                                )
                        
                        # Save Optimized cycle in DB
                        db_optmized_cycle = DBOptimizedCycles(
                            sequence_id=cycle.sequence_id,
                            serial_number=cycle.serial_number,
                            current_start_time=cycle.scheduled_start_time,
                            optimized_start_time=cycle.new_scheduled_start_time,
                            optimized_end_time=cycle.new_expected_end_time,
                            auto_management=cycle.auto_management,
                            flex_type=flex_type,
                            accepted_by_user=False,
                            flex_id=flex_id
                        )
                        db.session.add(db_optmized_cycle)
                        db.session.commit()
        
        outputs = []
        for output in shiftable_cycles_result:
            outputs.append(ScheduleResponse(
                serial_number=output.serial_number,
                sequence_id=output.sequence_id,
                schedule=output.schedule
            ))
            
        return outputs, 200, self.x_correlation_id
    
    def outputs_flexibility(self, result_opt_baseline, result_opt_flexibility, has_baseline, has_flexibility):

        baseline = []
        for item in result_opt_baseline.energy_consumption:
            logger.debug(item, extra=self.x_correlation_id)
            for key, value in item.items():
                baseline.append( 
                    {
                    "start_time": key,
                    "power_value": value,
                    "power_units": "kW"
                }
                )
        
        flexibility_downward = []
        for item in result_opt_baseline.aggregated_appliances_consumption:
            for key, value in item.items():
                flexibility_downward.append( 
                    {
                    "start_time": key,
                    "power_value": value,
                    "power_units": "kW"
                }
                )

        flexibility_upward = []
        for item in result_opt_flexibility.aggregated_appliances_consumption:
            for key, value in item.items():
                flexibility_upward.append( 
                    {
                    "start_time": key,
                    "power_value": value,
                    "power_units": "kW"
                }
                )

        flex_id, _ = save_available_flexibility(
            user_id=self.user_id, 
            baseline=result_opt_baseline.energy_consumption, 
            flexibility_upward=result_opt_flexibility.aggregated_appliances_consumption,
            flexibility_downward=result_opt_baseline.aggregated_appliances_consumption,
            has_baseline=has_baseline,
            has_flexibility=has_flexibility,
            x_correlation_id=self.x_correlation_id
            )

        outputs = {
            "user_id": self.user_id,
            "baseline": baseline,
            "flexibility_downward":flexibility_downward,
            "flexibility_upward":flexibility_upward
        }
        
        logger.debug("Outputs:", extra=self.x_correlation_id)
        logger.debug(outputs, extra=self.x_correlation_id)

            
        return outputs, 200, self.x_correlation_id, flex_id
    
    def outputs_with_zeros(self):

        list_zeros = []
       
        ts_key = self.start_date
        for _ in range(Config.PERIODS):
            list_zeros.append( {ts_key.strftime(Config.TIMESTAMP_FORMAT): 0.0} )
            ts_key += timedelta(minutes=int(Config.DELIVERY_TIME))
            
        result = SimpleNamespace()
        result.energy_consumption = list_zeros
        result.aggregated_appliances_consumption = list_zeros
        
        return result
