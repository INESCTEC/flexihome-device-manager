# coding: utf-8 
# Version: 1.1
#==============================================================================
#   Interconnect project - Flexibility Manager Service
#   Developer: Igor Rezende igorezc@gmail.com
#   Date: Sept 2022
#==============================================================================

import json
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from energy_manager_service import Config


# Non time dependent default data
LOAD_DEFAULT_PU  = [
                    0.20832,
                    0.1056,
                    0.09792,
                    0.08736,
                    0.09696,
                    0.22176,
                    0.36672,
                    0.5808,
                    0.54432,
                    0.45408,
                    0.3744,
                    0.38688,
                    0.44064,
                    0.44448,
                    0.30144,
                    0.28608,
                    0.40504,
                    0.4944,
                    0.60096,
                    0.5856,
                    0.5136,
                    0.42048,
                    0.27936,
                    0.25152
                ]
EMISSION_DEFAULT = [
            58.305913989468685,
            53.99440108649161,
            56.464655026291254,
            71.88826562063339,
            56.00363613162176,
            64.92143527352437,
            64.28963684437869,
            62.97503981429763,
            52.22258332069039,
            56.58950445889222,
            53.916868736654465,
            53.21161958847902,
            48.83646612977961,
            53.568118819109614,
            66.97032135064504,
            73.25779808173957,
            62.09804478113777,
            59.8104955574717,
            55.47390747380405,
            55.58970249823591,
            62.53913512325437,
            59.25063230571281,
            62.54976246200234,
            72.93782122667773]
PRICES_DEFAULT   = [
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.2337, 
                0.1696, 
                0.1696, 
                0.1696, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044, 
                0.1044]


class Default_data:
    
    def __init__(self, mock_sentinel_api_response=False):
        
        # Date used when mocking the cycles
        self.current_date_utc = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
        
        # Default data
        self.CONTRACTED_POWER = float(6.9)
        self.PRICES_BUY  = PRICES_DEFAULT
        self.PRICES_SELL = [int(0)] * Config.PERIODS
        self.FORECAST_PRODUCTION  = [int(0)] * Config.PERIODS
        
        self.FORECAST_CONSUMPTION = self.__mock_forecast_consumption()
        
        self.CO2_EMISSION = self.__mock_co2_emission(mock_sentinel_api_response)
        
        self.__mock_whirlpool_cycles()
    
    
    def __mock_forecast_consumption(self):
        forecast_consumption = []
        for dt in range(len(LOAD_DEFAULT_PU)): 
            value_p = LOAD_DEFAULT_PU[dt]/int(60 / Config.DELIVERY_TIME)* self.CONTRACTED_POWER
            value_p = round(value_p, Config.DECIMAL)
            
            forecast_consumption.extend([value_p] * int(60 / Config.DELIVERY_TIME))
        
        return forecast_consumption

    def __mock_co2_emission(self, as_sentinel_response=False):
        co2_emissions = []
        for dt in range(len(EMISSION_DEFAULT)): 
            co2_emissions.extend([EMISSION_DEFAULT[dt]] * int(60 / Config.DELIVERY_TIME))
        
        if as_sentinel_response:
            dt_now = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
            data = []
            for emission in co2_emissions:
                data.append({
                    "datetime": dt_now.strftime(Config.TIMESTAMP_FORMAT),
                    "request": datetime.now(timezone.utc).strftime(Config.TIMESTAMP_FORMAT),
                    "value": emission,
                    "unit": "gCO2eq/kWh",
                    "quality": 0,
                    "updated_at": datetime.now(timezone.utc).strftime(Config.TIMESTAMP_FORMAT)
                })
                
                dt_now = dt_now + timedelta(hours=1)
            
            response = {
                "data": data,
                "next_url": "null",
                "process_time": "0.0s",
                "rc": 0
            }
            
        else:
            response = co2_emissions
                
        
        return response
    
    def __mock_whirlpool_cycles(self):
        self.DEVICE_WP_CYCLES_1 = [{
            'serial_number': 'Hotpoint_FabricCare_WPR4LLLG8NWD4',
            'cycles': [
            {
                'sequence_id': '02LL221-AE2F-412A-A7ST-028KKL22HF',
                'earliest_start_time': self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),
                'latest_end_time': self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT), 
                'scheduled_start_time': self.current_date_utc.replace(hour=10,minute=18,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),
                'expected_end_time': self.current_date_utc.replace(hour=11,minute=32,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),
                'program': 'easy_care',
                'is_scheduled': "True",
                'is_optimized': "True",
                'power_profile': [
                {
                    'slot': 1,
                    'max_power': 200,
                    'power_units': 'W',
                    'duration': 13,
                    'duration_units': 'minutes'
                },
                {
                    'slot': 2,
                    'max_power': 1000,
                    'power_units': 'W',
                    'duration': 47,
                    'duration_units': 'minutes'
                },
                {
                    'slot': 3,
                    'max_power': 100,
                    'power_units': 'W',
                    'duration': 14,
                    'duration_units': 'minutes'
                }
                ]
            }
            ]
        }]
        self.DEVICE_WP_CYCLES_2 = [{
                "cycles": [
                    {
                        "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-16T10:46:05Z",
                        "expected_end_time": self.current_date_utc.replace(hour=11,minute=15,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T17:21:58Z",
                        "is_optimized": "False",
                        "latest_end_time": self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T17:21:58Z",
                        "power_profile": [
                            {
                                "duration": 47.0,
                                "duration_units": "minutes",
                                "max_power": 2600.0,
                                "power_units": "W",
                                "slot": 2
                            },
                            {
                                "duration": 3.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 4
                            },
                            {
                                "duration": 21.0,
                                "duration_units": "minutes",
                                "max_power": 1000.0,
                                "power_units": "W",
                                "slot": 3
                            },
                            {
                                "duration": 4.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 1
                            }
                        ],
                        "program": "WashCycleAntiStain-13",
                        "scheduled_start_time": self.current_date_utc.replace(hour=10,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T16:21:58Z",
                        "sequence_id": "Timer:WPR4LLLG8NWD4:1678962130588:CNC"
                    },
                    {
                        "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-16T10:46:12Z",
                        "expected_end_time": self.current_date_utc.replace(hour=15,minute=17,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T21:57:19Z",
                        "is_optimized": "False",
                        "latest_end_time": self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T21:57:19Z",
                        "power_profile": [
                            {
                                "duration": 68.0,
                                "duration_units": "minutes",
                                "max_power": 2600.0,
                                "power_units": "W",
                                "slot": 2
                            },
                            {
                                "duration": 3.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 4
                            },
                            {
                                "duration": 42.0,
                                "duration_units": "minutes",
                                "max_power": 1000.0,
                                "power_units": "W",
                                "slot": 3
                            },
                            {
                                "duration": 4.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 1
                            }
                        ],
                        "program": "WashCycleWool-7",
                        "scheduled_start_time": self.current_date_utc.replace(hour=13,minute=20,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T20:22:19Z",
                        "sequence_id": "Timer:WPR4LLLG8NWD4:1678962150342:CNC"
                    }
                ],
                "serial_number": "Hotpoint_FabricCare_WPR4LLLG8NWD4"
            }]
        self.DEVICE_WP_CYCLES_3 = [{
                "cycles": [
                                {
                        "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-16T10:46:05Z",
                        "expected_end_time": self.current_date_utc.replace(hour=11,minute=15,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T17:21:58Z",
                        "is_optimized": "False",
                        "latest_end_time": self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T17:21:58Z",
                        "power_profile": [
                            {
                                "duration": 47.0,
                                "duration_units": "minutes",
                                "max_power": 2600.0,
                                "power_units": "W",
                                "slot": 2
                            },
                            {
                                "duration": 3.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 4
                            },
                            {
                                "duration": 21.0,
                                "duration_units": "minutes",
                                "max_power": 1000.0,
                                "power_units": "W",
                                "slot": 3
                            },
                            {
                                "duration": 4.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 1
                            }
                        ],
                        "program": "WashCycleAntiStain-13",
                        "scheduled_start_time": self.current_date_utc.replace(hour=10,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T16:21:58Z",
                        "sequence_id": "Timer:WPR4LLLG8NWD4:1678962130588:CNC"
                    },
                    {
                        "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-16T10:46:12Z",
                        "expected_end_time": self.current_date_utc.replace(hour=15,minute=17,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T21:57:19Z",
                        "is_optimized": "False",
                        "latest_end_time": self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T21:57:19Z",
                        "power_profile": [
                            {
                                "duration": 68.0,
                                "duration_units": "minutes",
                                "max_power": 2600.0,
                                "power_units": "W",
                                "slot": 2
                            },
                            {
                                "duration": 3.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 4
                            },
                            {
                                "duration": 42.0,
                                "duration_units": "minutes",
                                "max_power": 1000.0,
                                "power_units": "W",
                                "slot": 3
                            },
                            {
                                "duration": 4.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 1
                            }
                        ],
                        "program": "WashCycleWool-7",
                        "scheduled_start_time": self.current_date_utc.replace(hour=13,minute=20,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T20:22:19Z",
                        "sequence_id": "Timer:WPR4LLLG8NWD4:1678962150342:CNC"
                    },
                    {
                        "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-16T10:46:18Z",
                        "expected_end_time": self.current_date_utc.replace(hour=17,minute=3,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T13:41:39Z",
                        "is_optimized": "False",
                        "latest_end_time": self.current_date_utc.replace(hour=23,minute=0,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T13:41:39Z",
                        "power_profile": [
                            {
                                "duration": 3.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 4
                            },
                            {
                                "duration": 71.0,
                                "duration_units": "minutes",
                                "max_power": 2600.0,
                                "power_units": "W",
                                "slot": 2
                            },
                            {
                                "duration": 4.0,
                                "duration_units": "minutes",
                                "max_power": 400.0,
                                "power_units": "W",
                                "slot": 1
                            },
                            {
                                "duration": 45.0,
                                "duration_units": "minutes",
                                "max_power": 1000.0,
                                "power_units": "W",
                                "slot": 3
                            }
                        ],
                        "program": "WashCycleWhites-33",
                        "scheduled_start_time": self.current_date_utc.replace(hour=15,minute=40,second=0,microsecond=0).strftime(Config.TIMESTAMP_FORMAT),#"2023-03-17T10:21:39Z",
                        "sequence_id": "Timer:WPR4LLLG8NWD4:1678962110124:CNC"
                    }
                ],
                "serial_number": "Hotpoint_FabricCare_WPR4LLLG8NWD4"
            }]

        return


    def mockdevice(self, user_id, cycles=1, brand = "WP"):
        #==============================================================================
        if (brand == "WP"):
            if (cycles == 1):
                appliance_ = self.DEVICE_WP_CYCLES_1
            elif (cycles == 2):
                appliance_ = self.DEVICE_WP_CYCLES_2
            elif (cycles == 3):
                appliance_ = self.DEVICE_WP_CYCLES_3
        #==============================================================================
        elif (brand == "BSH"):
            appliance_ = [
                {
                'serial_number': 'Hotpoint_FabricCare_WPR4LLLG8NWD4',
                'cycles': [{
                    "earliest_start_time": self.current_date_utc.replace(hour=6,minute=0,second=0).strftime(Config.TIMESTAMP_FORMAT), #"2022-09-23T10:32:52.576107Z",
                    "expected_end_time": self.current_date_utc.replace(hour=14,minute=48,second=0).strftime(Config.TIMESTAMP_FORMAT),
                    "is_optimized": "False",
                    "latest_end_time": self.current_date_utc.replace(hour=17,minute=0,second=0).strftime(Config.TIMESTAMP_FORMAT),
                    "power_profile": [
                    {
                    "duration": 228.0,
                    "duration_units": "minutes",
                    "expected_power": 1200.0,
                    "max_power": 2400.0,
                    "min_power": 300.0,
                    "power_units": "W",
                    "slot": 1
                    }
                    ],
                    "program": "bosch",
                    "scheduled_start_time": self.current_date_utc.replace(hour=11,minute=0,second=0).strftime(Config.TIMESTAMP_FORMAT),
                    "sequence_id": "<http://example.org/spine-ssa/devices/BOSCH-WTX87M40-68A40E90861C/powerSequences/1>"
                        }]
                },
                {
                "cycles": [],
                "serial_number": "BOSCH-WTX87M40-68A40E90861C"
                },
                {
                "cycles": [],
                "serial_number": "WPR4LLLG8NWD4"
                },
                {
                "cycles": [],
                "serial_number": "BOSCH-WAL28PH1ES-68A40E94451D"
                },
                {
                "cycles": [],
                "serial_number": "000106087175"
                }
                ]
        #==============================================================================
        pooldemo_resp = {
            'user_id': f'{user_id}',
            'cycles':appliance_
                }
        pooldemo_resp = str(pooldemo_resp).replace("'", '"')
        pooldemo_resp = json.loads(pooldemo_resp, object_hook=lambda d: SimpleNamespace(**d))
        #==============================================================================
        return pooldemo_resp
      #==============================================================================
################################################################################################
