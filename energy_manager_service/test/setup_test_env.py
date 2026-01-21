"""
Test environment is composed of the following containers:
    # DATABASES
    - postgresql
        - docker-compose up postgresql
    - cassandra
        - docker-compose up cassandra cassandra-load-keyspace
    
    # KAFKA STACK
    - zookeeper
    - kafka
    - connect (with account manager connector)
        - docker-compose up zookeeper kafka connect
        - curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ --data-binary "@connectors/account_manager.json"
    
    # GENERIC ADAPTER (SIF)
    - ga
    - ga-wp
        - docker-compose up ga ga-wp
    
    # HEMS SERVICES
    - account manager
        - docker-compose up account-manager
    - device manager
        - docker-compose up device-manager
    - energy prices
        - docker-compose up energy-prices
    - notification service
        - docker-compose up notification-service
    - forecast rest api
        - docker-compose up forecast-rest-api

Goal of this script:
    To setup the test environment with the required data to run the energy manager optimizer:
        - Register, confirm and login a user
            - Give the user a valid expo token
        - Create a forecast installation for the user
        - Insert mock forecast data for the user
        - Add a device and schedule a cycle
        - Insert mock data for the energy prices 
        
Pre-requisites:
    - Have all the containers running
    
    
TODO:
    - Mock energy prices data
    
    
Possible issues:
    - Device Manager:
        - Sometimes database sessions get stuck in state (idle in transaction) and the database gets locked
        - SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'devicemanager'
            AND pid <> pg_backend_pid();
        - Will purge all sessions active in the database
"""
import requests, uuid, json, psycopg2, sys
import numpy as np
from time import sleep
from random import randint
from datetime import datetime, timedelta

from cassandra.cluster import Cluster

sys.path.append("..")

from energy_manager_service.test.config import Config
# from config import Config

# from clear_database import clear_energy_prices_db


# Cassandra connection

# cluster = Cluster()
# cass_session = cluster.connect('forecast_test')


# # Database connection

# conn_account = psycopg2.connect(
#     database = "account_manager", 
#     user = Config.DATABASE_USER, 
#     host= Config.DATABASE_IP,
#     password = Config.DATABASE_PASSWORD,
#     port = Config.DATABASE_PORT
# )

# conn_prices = psycopg2.connect(
#     database = "energyprices", 
#     user = Config.DATABASE_USER, 
#     host= Config.DATABASE_IP,
#     password = Config.DATABASE_PASSWORD,
#     port = Config.DATABASE_PORT
# )

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY


def register_user(email, meter_id):
    
    headers = {
        "X-Correlation-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    password = "654321"
    user_register_body = {
        "first_name": "Staging",
        "last_name": "Test",
        "email": email,
        "password": password,
        "password_repeat": password,
        "meter_id": meter_id,
        "country": "PT",
        "postal_code": "4455-001",
        "tarif_type": "bi-hourly",
        "contracted_power": "6.9 kVA",
        "schedule_type": "economic"
    }

    r = requests.post(
        url=f'{Config.ACCOUNT_MANAGER_ENDPOINT}/register',
        headers=headers,
        json=user_register_body
    )
    r.raise_for_status()

    user = json.loads(r.content.decode('utf-8'))
    print(f"User ID: {user['user_id']}")
    
    print(f"User registered... {r.status_code}")
    
    return user
    
    
def confirm_user(user_id):
    conn_account = psycopg2.connect(
        database = "account_manager", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
    
    tries = 0
    max_tries = 3

    with conn_account:
        with conn_account.cursor() as cur:
            while tries < max_tries:
                cur = conn_account.cursor()
                cur.execute(f'SELECT token FROM confirmation_tokens WHERE user_id = \'{user_id}\';')
                token = cur.fetchone()
                
                if token is not None:
                    token = token[0]
                    break
                
                sleep(5)
                tries += 1

    r = requests.post(
        url=f'{Config.ACCOUNT_MANAGER_ENDPOINT}/confirm-account/{token}'
    )
    r.raise_for_status()

    print(f"User Confirmed... {r.status_code}")
    
    return


def user_login(email, password, expo_token = None):
    
    if expo_token is not None:
        headers = {
            "X-Correlation-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "expo-token": expo_token
        }
    else:
        headers = {
            "X-Correlation-ID": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }


    login_body = {
        "email": email,
        "password": password
    }
    r = requests.post(
        url=f'{Config.ACCOUNT_MANAGER_ENDPOINT}/login',
        headers=headers,
        json=login_body
    )
    r.raise_for_status()
    
    auth_token = r.headers['Authorization']
    print(auth_token)

    print(f"User logged in... {r.status_code}")
    
    return auth_token


def user_register_and_login(email, meter_id):
    user = register_user(email, meter_id)
    
    user_id = user['user_id']
    confirm_user(user_id)
    
    auth_token = user_login(email, password="654321", expo_token="Vx0UOnHepDooEcudAixJvb")
    
    return user_id, auth_token


def add_device(auth_token, brand, serial_number):
    headers = {
        "X-Correlation-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Authorization": auth_token
    }
    
    query_params = {
        "brand": brand
    }
    
    add_device_body = {
        "serial_number": serial_number
    }
    
    r = requests.post(
        url=f'{Config.DEVICE_MANAGER_ENDPOINT}/device',
        headers=headers,
        params=query_params,
        json=add_device_body
    )
    r.raise_for_status()
    
    device = json.loads(r.content.decode('utf-8'))
    
    print(f"Device added... {r.status_code}")
    
    return device


def set_automatic_management_of_device(auth_token, serial_number):
    headers = {
        "X-Correlation-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Authorization": auth_token
    }
    
    query_params = {
        "serial_number": serial_number
    }
    
    r = requests.post(
        url=f'{Config.DEVICE_MANAGER_ENDPOINT}/device/settings/set-automatic-management',
        headers=headers,
        params=query_params
    )
    r.raise_for_status()
    
    print(f'Automatic management set to false... {r.status_code}')
    
    return
    

def schedule_cycle(auth_token, serial_number, start_time = None):
    if start_time is None:
        start_time = (datetime.now().replace(hour=0) + timedelta(days=1, hours=12)).isoformat()
    
    
    headers = {
        "X-Correlation-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Authorization": auth_token
    }
    
    query_params = {
        "serial_number": serial_number
    }
    
    schedule_cycle_body = {
        "scheduled_start_time": start_time,
        "program": "cotton"
    }
    
    r = requests.post(
        url=f'{Config.DEVICE_MANAGER_ENDPOINT}/schedule-cycle-by-device',
        headers=headers,
        params=query_params,
        json=schedule_cycle_body
    )
    r.raise_for_status()
    
    cycle = json.loads(r.content.decode('utf-8'))
    
    print(f"Cycle scheduled... {r.status_code}")
    
    return cycle


def mock_energy_prices(step=96, days_delta=0):
    conn_prices = psycopg2.connect(
        database = "energyprices", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
    
    
    
    with conn_prices:
        with conn_prices.cursor() as cur:
            cur = conn_prices.cursor()
            
            try:
                cur.execute("SELECT id FROM db_price_per_time ORDER BY id DESC LIMIT 1;")
                last_id = cur.fetchone()
                # print(last_id)
                last_id = last_id[0]
                
                cur.execute("SELECT id FROM db_energy_prices ORDER BY id DESC LIMIT 1;")
                prices_last_id = cur.fetchone()
                # print(prices_last_id)
                prices_last_id = prices_last_id[0]
            
            except Exception as e:
                print(repr(e))
                last_id = 0
                prices_last_id = 0
            
            # print(prices_last_id)
            cur.execute(f'INSERT INTO db_energy_prices(id,tarif_type,contracted_power,contracted_power_units,price_type,\"eventType\") VALUES({1+prices_last_id},\'{"bi-hourly"}\',{6.9},\'{"kva"}\',\'{"active-energy"}\',\'{"kva-low"}\')')
            
            dt = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0) + timedelta(days=days_delta)
            for i in range(step):
                db_id = i+1+last_id
                cur.execute(f'INSERT INTO db_price_per_time (id,timestamp,price,units,energy_price_ref) VALUES({db_id},\'{dt.isoformat()}\',{0.1578},\'{"€/kWh"}\',{1})')
                
                dt = dt + timedelta(minutes=15)
                

            cur.execute(f'INSERT INTO db_energy_prices(id,tarif_type,contracted_power,contracted_power_units,price_type,\"eventType\") VALUES({2+prices_last_id},\'{"bi-hourly"}\',{6.9},\'{"kva"}\',\'{"standing-charges"}\',\'{"kva-low"}\')')
            
            dt = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0) + timedelta(days=days_delta)
            for i in range(step):
                db_id = i+step+1+last_id
                cur.execute(f'INSERT INTO db_price_per_time (id,timestamp,price,units,energy_price_ref) VALUES({db_id},\'{dt.isoformat()}\',{0.1578},\'{"€/kWh"}\',{2})')
                
                dt = dt + timedelta(minutes=15)
            
    print("Mock energy prices insert into db...")
    
    return
    
    
def mock_forecast(user_id, step=24):
    cluster = Cluster()
    cass_session = cluster.connect('forecast_test')

    # Populate nwp_grid
    dt = datetime.now()
    for lat, long in zip(range(36, 43), np.linspace(-9, -7, 7)):
        cass_session.execute(
            """
            INSERT INTO nwp_grid (source, latitude, longitude, inserted_at, is_active, last_request, last_updated, variables)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("source", lat, long, dt, 1, dt, dt, "aaa")
        )
    
    sleep(2)
    
    # Register installation
    
    installation_body = {
        "installation_code": f"{user_id}_consumption",
        "country": "portugal",
        "generation": 0,
        "installation_type": "load",
        "latitude": 41.1336,
        "longitude": -8.6174,
        "net_power_types": "PQ",
        "source_nwp": "wrf_12km",
        "is_active": 1,
        "installed_capacity": 3.45
    }
    
    r = requests.post(
        url=f'{Config.FORECAST_ENDPOINT_TEST}/api/installations/register',
        json=installation_body
    )
    print(r.content)
    
    print("Mock forecast installation registered...")

    # Mock forecast data for user
    
    dt = (datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0)) + timedelta(days=1)
    for _ in range(step):
        cass_session.execute(
            """
            INSERT INTO forecast (id, register_type, datetime, request, algorithm, horizon, last_updated, model_info, q05, q10, q20, q30, q40, q50, q60, q70, q80, q90, q95, units)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s, %s)
            """,
            (f"{user_id}_consumption", "P", dt, dt, "naive", "D+1", dt, "naive", None, None, None, None, None, randint(0, 3000), None, None, None, None, None, None)
        )
        
        dt = dt + timedelta(hours=1)

    print("Mock forecast data added...")
    
    return
    

def setup_test_env(email = "vascampos25+test@gmail.com", meter_id = METER_ID, serial_number = "serialnumbertest", set_auto = False, second_user = False):
    """Sets up a test environment with one user, one device and one cycle.

    Returns:
        str: the test user id
    """
    user_id, auth_token = user_register_and_login(email, meter_id)
    
    device = add_device(auth_token, brand="Bosch", serial_number=serial_number)
    
    if set_auto is False:
        set_automatic_management_of_device(auth_token, serial_number)
    
    cycle = schedule_cycle(auth_token, serial_number)
    
    mock_forecast(user_id)
    
    return user_id, auth_token, device, cycle
    

if __name__ == "__main__":
    setup_test_env()
