from types import SimpleNamespace
from pyscipopt import Model, quicksum

from energy_manager_service import Config, logger, generalLogger
from energy_manager_service.utils.date.datetime import index_to_datetime


class CO2Scheduler():
    
    def __init__(self, input_class):
        
        self.start_date = input_class.start_date
        
        # Create solver instance
        self.model_scip = Model()
        self.model_scip.hideOutput()
        
        # Initialize inputs requeriments
        self.prices_buy          = input_class.prices_buy[0:Config.PERIODS]
        self.prices_sell         = input_class.prices_sell[0:Config.PERIODS]
        self.consumption_value_p = input_class.consumption_value_p[0:Config.PERIODS]
        self.production_value_p  = input_class.production_value_p[0:Config.PERIODS]
        self.power_limit         = input_class.contracted_power_value
        self.pool_appliances     = input_class.pool_appliances
        
        # Initialize outputs requeriments
        self.result = []
        
    def __call__(self, cor_id):
        log_message = 'The optimization problem is running'
        logger.info(log_message, extra=cor_id)
        
        # Build problem formulation
        self.result = self.scip_formulation()
        
        log_message = 'Generate a schedule with the activated flexibility'
        logger.info(log_message, extra=cor_id)

        return self.result
    

    # SCIP PROBLEM FORMULATION
    def scip_formulation(self):
        
        # Shiftable Cycles info
        shiftable_appliance_info = self.constrains_shiftable_flex()
        
        #==============================================================================
        # Objetive function
        #==============================================================================
        ENERGY_BUY_VARBASENAME  = "Y_b"  # grid-consumption
        ENERGY_SELL_VARBASENAME = "Y_s"  # self-consumption
        
        energy_buy  = []
        energy_sell = []
        for dt in range(Config.PERIODS):
            # Y < 0 ----> consumption
            energy_buy_var = self.model_scip.addVar(
                ENERGY_BUY_VARBASENAME + "_" + str(dt), 
                vtype = 'C', 
                lb = 0.0, 
                ub=None
            )
            energy_buy.append(energy_buy_var)
            
            # Y > 0  ----> export production
            energy_sell_var = self.model_scip.addVar(
                ENERGY_SELL_VARBASENAME + "_" + str(dt), 
                vtype = 'C', 
                lb = 0.0, 
                ub=None
            )
            energy_sell.append(energy_sell_var) 
            
        self.model_scip.setObjective(
            quicksum(energy_buy[dt] * self.prices_buy[dt] - energy_sell[dt] * self.prices_sell[dt] for dt in range(Config.PERIODS)), 
            "minimize"
        )


        # Constrains
        
        # 1 - Binary constrain:
        BINARY_VARBASENAME = "b"
        INFINITE = float(9 * pow(10, 9))
        for dt in range(Config.PERIODS):
            # binary for the constraint
            binary_var = self.model_scip.addVar(
                f"{BINARY_VARBASENAME}_{dt}", 
                vtype = 'B', 
                lb = 0.0, 
                ub = 1
            )  
            
            self.model_scip.addCons(
                energy_sell[dt] <= INFINITE * binary_var, 
                name = f"bin_sell_{dt}"
            ) 
            self.model_scip.addCons(
                energy_buy[dt] <= (1 - binary_var) * INFINITE, 
                name = f"bin_buy_{dt}"
            )

        # 2 - Power limit constrain:
        for dt in range(Config.PERIODS):
            self.model_scip.addCons(
                energy_buy[dt] <= self.power_limit, 
                name = f"ContractedPower_{dt}"
            ) 

        # 3 - Balance constrain:       
        for dt in range(Config.PERIODS):
            constrain_balance =  energy_sell[dt] - energy_buy[dt] 
            constrain_balance -= self.production_value_p[dt] 
            constrain_balance += self.consumption_value_p[dt]

            # Shiftable Cycles info
            for cycles in shiftable_appliance_info:
                for cycles_info in cycles:
                    constrain_balance += cycles_info.constrain_balance[dt]

            self.model_scip.addCons(
                constrain_balance == 0, 
                name = f"Balance_{dt}"
            )

        self.model_scip.setRealParam('limits/gap', 0.0)

        # Solve problem 
        self.model_scip.optimize()

        # Get outputs problem 
        scip_results = self.scip_output(
            energy_buy,
            energy_sell,
            shiftable_appliance_info
        )

        return scip_results

    def scip_output(self, energy_buy, energy_sell, shiftable_appliance_info):
        
        solution = self.model_scip.getBestSol()

        # Get variables values
        shiftable_cycles_result = None
        if self.model_scip.getStatus() == "optimal":

            # Energy buy
            result_energy_buy = []
            for dt, var in enumerate(energy_buy):
                timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                result_var = self.model_scip.getVal(var)
                result_energy_buy.append({timestamp:result_var})

            # Energy sell 
            result_energy_sell = []
            for dt, var in enumerate(energy_sell):
                timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                result_var = self.model_scip.getVal(var)
                result_energy_sell.append({timestamp:result_var})

        # Get shiftable appliances variables values
            shiftable_cycles_result = []
            shiftable_slots_result  = []
            for cycles in shiftable_appliance_info:
                for cycles_info in cycles:
                    
                    schedule_ = []
                    result_cycle = SimpleNamespace()
                    for slot in range(len(cycles_info.consumption_expected)):
                        for dt in range(slot, Config.PERIODS - (len(cycles_info.consumption_expected) - 1 - slot), 1):
                            
                            var_ = cycles_info.binary[slot][dt]
                            if (type(var_) != type(int())):
                                result_var = self.model_scip.getVal(cycles_info.binary[slot][dt])
                                
                                if result_var != 0: 
                                    timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                                    shiftable_slots_result.append({cycles_info.basename_list[slot]:timestamp})
                                    schedule_.append(dt)
                                    break
                                
                    result_cycle.serial_number = cycles_info.serial_number
                    result_cycle.sequence_id = cycles_info.sequence_id
                    result_cycle.schedule    = schedule_ 
                    shiftable_cycles_result.append(result_cycle)

        return shiftable_cycles_result


    ################################################################################################
    #   Shiftable APPLIANCES MODEL -- used to build constrains
    ################################################################################################
    def constrains_shiftable_flex(self):
        
        appliances_info = []
        for app_idx, cycles_in_pool in enumerate(self.pool_appliances):
            
            cycles_info = []
            constrain_dt_list = []
            
            for cycle_idx, cycle in enumerate(cycles_in_pool):
                cycle_basename = f"Shift{app_idx}C{cycle_idx}"
                resp_class = self.constrains_continuous_mode(  
                    cycle_basename,
                    cycle,
                )
                cycles_info.append(resp_class)
                constrain_dt_list.append(resp_class.constrain_dt_cycle)

            list_1 = [0] * Config.PERIODS
            for list_2 in constrain_dt_list:
                constrain_dt_cycle = [value_1 + value_2 for value_1, value_2 in zip(list_1, list_2)]
                list_1 = constrain_dt_cycle
            for dt, constrain_value in enumerate(constrain_dt_cycle):
                for key in constrain_value.terms:
                    aux = constrain_value.terms[key]
                if (aux != 0):
                    self.model_scip.addCons(
                        constrain_value <= 1 , 
                        name = f"DeliveryTime_{dt}"
                        )

            appliances_info.append(cycles_info)

        return appliances_info
    

    def constrains_continuous_mode(self, cycle_basename, cycle):
        
        MAXTIME_PAUSE = 1
        class_output = SimpleNamespace()
        start_limit = cycle.window_limits[0]
        end_limit   = cycle.window_limits[1]
        consumption_expected = cycle.consumption_expected
        num_slots = len(consumption_expected)

        # Binary constrains of cycle 
        binary = [0] * num_slots
        basename_list = []
        for slot in range(num_slots):
            binary[slot] = [0] * Config.PERIODS
            slot_basename = f"{cycle_basename}_st{slot+1}"
            basename_list.append(slot_basename)
            
            for dt in range(slot + start_limit, end_limit - (num_slots - 1 - slot), 1):
                binary[slot][dt]   = self.model_scip.addVar(
                    name  = f"{slot_basename}_dt{dt}", 
                    vtype = 'B', 
                    lb    = float(0), 
                    ub    = float(1)
                )

        constrain_dt_cycle = []
        constrain_balance = []
        for dt in range(Config.PERIODS):
            constrain_dt_cycle.append(quicksum(binary[slot][dt] for slot in range(num_slots)))
            constrain_balance.append(quicksum(binary[slot][dt] * consumption_expected[slot] for slot in range(num_slots)))
        
        for slot in range(num_slots - 1):
            window_1 = quicksum(binary[slot][dt] * dt for dt in range(Config.PERIODS))
            for key in window_1.terms:
                aux1 = window_1.terms[key]
            window_2 = quicksum(binary[slot + 1][dt] * dt for dt in range(Config.PERIODS))
            for key in window_2.terms:
                aux2 = window_2.terms[key]
            if (aux1 != 0 and 
            aux2 != 0):
                self.model_scip.addCons(
                    window_2 - window_1 >= 0, 
                    name = f"{cycle_basename}_Sequence{slot}-{slot+1}"
                )
                self.model_scip.addCons(
                    window_2 - window_1 <= MAXTIME_PAUSE, 
                    name = f"{cycle_basename}_Pause{slot}-{slot+1}"
                )
                
        for slot in range(num_slots):
            self.model_scip.addCons(
                quicksum(binary[slot][dt] for dt in range(Config.PERIODS)) == 1, 
                name = f"{cycle_basename}_st{slot}"
            )
            
        class_output.serial_number   = cycle.serial_number
        class_output.sequence_id = cycle.sequence_id
        class_output.constrain_dt_cycle = constrain_dt_cycle
        class_output.constrain_balance = constrain_balance
        class_output.binary = binary
        class_output.basename_list = basename_list
        class_output.consumption_expected = consumption_expected
        
        return class_output


class FlexibilityScheduler():
    
    def __init__(self, input_class):
        
        self.start_date = input_class.start_date
        
        # Create solver instance
        self.model_scip = Model()
        self.model_scip.hideOutput()
        
        # Initialize inputs requeriments
        self.prices_buy          = input_class.weight_buy[0:Config.PERIODS]
        self.prices_sell         = input_class.weight_sell[0:Config.PERIODS]
        self.consumption_value_p = input_class.consumption_value_p[0:Config.PERIODS]
        self.production_value_p  = input_class.production_value_p[0:Config.PERIODS]
        self.power_limit         = input_class.contracted_power_value
        self.pool_appliances     = input_class.pool_appliances
        
        # Initialize outputs requeriments
        self.result = []
        
    def __call__(self, cor_id):
        log_message = 'The optimization problem is running'
        logger.info(log_message, extra=cor_id)
        
        # Build problem formulation
        self.result = self.scip_formulation()
        
        log_message = 'Generate a schedule with the activated flexibility'
        logger.info(log_message, extra=cor_id)

        return self.result
    

    # SCIP PROBLEM FORMULATION
    def scip_formulation(self):
        
        # Shiftable Cycles info
        shiftable_appliance_info = self.constrains_shiftable_flex()
        
        #==============================================================================
        # Objetive function
        #==============================================================================
        ENERGY_BUY_VARBASENAME  = "Y_b"  # grid-consumption
        ENERGY_SELL_VARBASENAME = "Y_s"  # self-consumption
        
        energy_buy  = []
        energy_sell = []
        for dt in range(Config.PERIODS):
            # Y < 0 ----> consumption
            energy_buy_var = self.model_scip.addVar(
                ENERGY_BUY_VARBASENAME + "_" + str(dt), 
                vtype = 'C', 
                lb = 0.0, 
                ub=None
            )
            energy_buy.append(energy_buy_var)
            
            # Y > 0  ----> export production
            energy_sell_var = self.model_scip.addVar(
                ENERGY_SELL_VARBASENAME + "_" + str(dt), 
                vtype = 'C', 
                lb = 0.0, 
                ub=None
            )
            energy_sell.append(energy_sell_var) 
            
        self.model_scip.setObjective(
            quicksum(energy_buy[dt] * self.prices_buy[dt] - energy_sell[dt] * self.prices_sell[dt] for dt in range(Config.PERIODS)), 
            "minimize"
        )


        # Constrains
        
        # 1 - Binary constrain:
        BINARY_VARBASENAME = "b"
        INFINITE = float(9 * pow(10, 9))
        for dt in range(Config.PERIODS):
            # binary for the constraint
            binary_var = self.model_scip.addVar(
                f"{BINARY_VARBASENAME}_{dt}", 
                vtype = 'B', 
                lb = 0.0, 
                ub = 1
            )  
            
            self.model_scip.addCons(
                energy_sell[dt] <= INFINITE * binary_var, 
                name = f"bin_sell_{dt}"
            ) 
            self.model_scip.addCons(
                energy_buy[dt] <= (1 - binary_var) * INFINITE, 
                name = f"bin_buy_{dt}"
            )

        # 2 - Power limit constrain:
        for dt in range(Config.PERIODS):
            self.model_scip.addCons(
                energy_buy[dt] <= self.power_limit, 
                name = f"ContractedPower_{dt}"
            ) 

        # 3 - Balance constrain:       
        for dt in range(Config.PERIODS):
            constrain_balance =  energy_sell[dt] - energy_buy[dt] 
            constrain_balance -= self.production_value_p[dt] 
            constrain_balance += self.consumption_value_p[dt]

            # Shiftable Cycles info
            for cycles in shiftable_appliance_info:
                for cycles_info in cycles:
                    constrain_balance += cycles_info.constrain_balance[dt]

            self.model_scip.addCons(
                constrain_balance == 0, 
                name = f"Balance_{dt}"
            )

        self.model_scip.setRealParam('limits/gap', 0.0)

        # Solve problem 
        self.model_scip.optimize()

        # Get outputs problem 
        scip_results = self.scip_output(
            energy_buy,
            energy_sell,
            shiftable_appliance_info
        )

        return scip_results

    def scip_output(self, energy_buy, energy_sell, shiftable_appliance_info):
        
        solution = self.model_scip.getBestSol()
        result_opt = SimpleNamespace()

        # Get variables values
        shiftable_cycles_result = None
        # TODO: Tem de haver um fallback para se o status for != optimal (fazer um else)
        if self.model_scip.getStatus() == "optimal":
            
            # Aggregated Appliances Consumption
            aggregated_appliances_consumption = []
            # Energy buy
            result_energy_buy = []
            for dt, var in enumerate(energy_buy):
                timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                result_var = self.model_scip.getVal(var)
                result_energy_buy.append({timestamp:result_var})

                aggregated_appliances_consumption.append({timestamp:0})

            # Energy sell 
            result_energy_sell = []
            for dt, var in enumerate(energy_sell):
                timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                result_var = self.model_scip.getVal(var)
                result_energy_sell.append({timestamp:result_var})

            # Get shiftable appliances variables values
            shiftable_cycles_result = []
            shiftable_slots_result  = []
            for cycles in shiftable_appliance_info:
                for cycles_info in cycles:
                    
                    schedule_ = []
                    result_cycle = SimpleNamespace()
                    for slot in range(len(cycles_info.consumption_expected)):
                        for dt in range(slot, Config.PERIODS - (len(cycles_info.consumption_expected) - 1 - slot), 1):
                            
                            var_ = cycles_info.binary[slot][dt]
                            if (type(var_) != type(int())):
                                result_var = self.model_scip.getVal(cycles_info.binary[slot][dt])
                                
                                if result_var != 0: 
                                    timestamp = index_to_datetime(self.start_date, dt).strftime(Config.TIMESTAMP_FORMAT)
                                    shiftable_slots_result.append({cycles_info.basename_list[slot]:timestamp})
                                    schedule_.append(dt)
                                    
                                    for item in aggregated_appliances_consumption:
                                        if timestamp in item:

                                            item[timestamp] += cycles_info.consumption_expected[slot]

                                    break
                                
                    result_cycle.serial_number = cycles_info.serial_number
                    result_cycle.sequence_id = cycles_info.sequence_id
                    result_cycle.schedule    = schedule_ 

                    shiftable_cycles_result.append(result_cycle)
        
        
            result_opt.energy_buy  = result_energy_buy
            result_opt.energy_sell = result_energy_sell
            generalLogger.debug(f"result_opt.energy_buy: {result_opt.energy_buy}")
            generalLogger.debug(f"result_opt.energy_sell: {result_opt.energy_sell}")
            # result_opt.energy_consumption = [list(item_buy.values())[0] - list(item_sell.values())[0] for item_buy, item_sell in zip(result_energy_buy, result_energy_sell)]
            result_opt.energy_consumption = []
            for item_buy, item_sell in zip(result_energy_buy, result_energy_sell):
                ts_buy, value_buy = item_buy.popitem()
                ts_sell, value_sell = item_sell.popitem()
                
                result_opt.energy_consumption.append({ts_buy: value_buy - value_sell})
                
            result_opt.aggregated_appliances_consumption = aggregated_appliances_consumption
            
            result_opt.shiftable_cycles_result = shiftable_cycles_result 
        
        
        else:
            result_opt = None
            generalLogger.debug(self.model_scip.getStatus())


        return result_opt


    ################################################################################################
    #   Shiftable APPLIANCES MODEL -- used to build constrains
    ################################################################################################
    def constrains_shiftable_flex(self):
        
        appliances_info = []
        for app_idx, cycles_in_pool in enumerate(self.pool_appliances):
            
            cycles_info = []
            constrain_dt_list = []
            
            for cycle_idx, cycle in enumerate(cycles_in_pool):
                cycle_basename = f"Shift{app_idx}C{cycle_idx}"
                resp_class = self.constrains_continuous_mode(  
                    cycle_basename,
                    cycle,
                )
                cycles_info.append(resp_class)
                constrain_dt_list.append(resp_class.constrain_dt_cycle)

            list_1 = [0] * Config.PERIODS
            for list_2 in constrain_dt_list:
                constrain_dt_cycle = [value_1 + value_2 for value_1, value_2 in zip(list_1, list_2)]
                list_1 = constrain_dt_cycle
            for dt, constrain_value in enumerate(constrain_dt_cycle):
                for key in constrain_value.terms:
                    aux = constrain_value.terms[key]
                if (aux != 0):
                    self.model_scip.addCons(
                        constrain_value <= 1 , 
                        name = f"DeliveryTime_{dt}"
                        )

            appliances_info.append(cycles_info)

        return appliances_info
    

    def constrains_continuous_mode(self, cycle_basename, cycle):
        
        MAXTIME_PAUSE = int(1)
        class_output = SimpleNamespace()
        start_limit = cycle.window_limits[0]
        end_limit   = cycle.window_limits[1]
        consumption_expected = cycle.consumption_expected
        num_slots = len(consumption_expected)

        # Binary constrains of cycle 
        binary = [0] * num_slots
        basename_list = []
        for slot in range(num_slots):
            binary[slot] = [0] * Config.PERIODS
            slot_basename = f"{cycle_basename}_st{slot+1}"
            basename_list.append(slot_basename)
            
            for dt in range(slot + start_limit, end_limit - (num_slots - 1 - slot), 1):
                binary[slot][dt]   = self.model_scip.addVar(
                    name  = f"{slot_basename}_dt{dt}", 
                    vtype = 'B', 
                    lb    = float(0), 
                    ub    = float(1)
                )
            #------------------------------------------------------------------------------
            # Flexibility call - exclude baseline schedule 
            if (cycle.baseline_schedule != None):
                for dt in cycle.baseline_schedule:
                    binary[slot][dt] = 0
        #==============================================================================
        for slot in range(num_slots):
            self.model_scip.addCons(
                quicksum(binary[slot][dt] for dt in range(Config.PERIODS)) == 1, 
                name = f"{cycle_basename}_st{slot}"
            )
        #------------------------------------------------------------------------------
        constrain_dt_cycle = []
        constrain_balance = []
        for dt in range(Config.PERIODS):
            constrain_dt_cycle.append(quicksum(binary[slot][dt] for slot in range(num_slots)))
            constrain_balance.append(quicksum(binary[slot][dt] * consumption_expected[slot] for slot in range(num_slots)))
        #==============================================================================
        # Sequence and Pause Constrains
        for slot in range(num_slots - 1):
            window_1 = quicksum(binary[slot][dt] * dt for dt in range(Config.PERIODS))
            for key in window_1.terms:
                aux1 = window_1.terms[key]
            window_2 = quicksum(binary[slot + 1][dt] * dt for dt in range(Config.PERIODS))
            for key in window_2.terms:
                aux2 = window_2.terms[key]
            if (aux1 != 0 and 
            aux2 != 0):
                #==============================================================================
                # Sequence Constrain
                self.model_scip.addCons(
                    window_2 - window_1 >= 0, 
                    name = f"{cycle_basename}_Sequence{slot}-{slot+1}"
                )
                #==============================================================================
                # Pause Constrain
                self.model_scip.addCons(
                    window_2 - window_1 <= MAXTIME_PAUSE, 
                    name = f"{cycle_basename}_Pause{slot}-{slot+1}"
                )
        #==============================================================================
        class_output.serial_number   = cycle.serial_number
        class_output.sequence_id = cycle.sequence_id
        class_output.constrain_dt_cycle = constrain_dt_cycle
        class_output.constrain_balance = constrain_balance
        class_output.binary = binary
        class_output.basename_list = basename_list
        class_output.consumption_expected = consumption_expected
        
        return class_output
