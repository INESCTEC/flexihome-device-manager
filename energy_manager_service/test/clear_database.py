import psycopg2, sys

from cassandra.cluster import Cluster

sys.path.append("..")

from energy_manager_service.test.config import Config
# from config import Config


def clear_account_manager_db(conn):
    
    with conn:
        with conn.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE users CASCADE;')
            cur.execute(f'TRUNCATE TABLE confirmation_tokens CASCADE;')
            cur.execute(f'TRUNCATE TABLE events CASCADE;')
            
    conn.close()
            

def clear_device_manager_db(conn_d):
    
    with conn_d:
        with conn_d.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE db_shiftable_machine CASCADE;')
            cur.execute(f'TRUNCATE TABLE db_not_disturbs CASCADE;')
            cur.execute(f'TRUNCATE TABLE db_dongles CASCADE;')
            cur.execute(f'TRUNCATE TABLE processed_events CASCADE;')
            
    conn_d.close()
            

def clear_energy_prices_db(conn_p):
        
        with conn_p:
            with conn_p.cursor() as cur:
                cur.execute(f'TRUNCATE TABLE erse_semi_processed_tariffs CASCADE;')
                cur.execute(f'TRUNCATE TABLE processed_events CASCADE;')
                # cur.execute(f'TRUNCATE TABLE db_processed_event CASCADE;')
        
        conn_p.close()
            

def clear_cassandra_db(session):
    
    session.execute("TRUNCATE forecast_test.installations;")
    session.execute("TRUNCATE forecast_test.nwp_grid;")
    session.execute("TRUNCATE forecast_test.models_info;")
    session.execute("TRUNCATE forecast_test.raw;")
    session.execute("TRUNCATE forecast_test.net;")
    session.execute("TRUNCATE forecast_test.forecast;")
    session.execute("TRUNCATE forecast_test.metrics_2wk;")
    session.execute("TRUNCATE forecast_test.metrics_year;")
    session.execute("TRUNCATE forecast_test.processed;")
    session.execute("TRUNCATE forecast_test.nwp_solar;")
    session.execute("TRUNCATE forecast_test.nwp_wind;")
    session.execute("TRUNCATE forecast_test.users_rest;")
    session.execute("TRUNCATE forecast_test.objects;")
    
    session.shutdown()
    

def clear_all_db():
    # Cassandra connection

    cluster = Cluster()
    cass_session = cluster.connect('forecast_test')
    

    conn_device = psycopg2.connect(
        database = "devicemanager", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
        
    print("Clearing device manager database...")
    clear_device_manager_db(conn_device)
    
    
    conn_account = psycopg2.connect(
        database = "account_manager", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
    
    print("Clearing account manager database...")
    clear_account_manager_db(conn_account)
    
    
    conn_prices = psycopg2.connect(
        database = "energyprices", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
    
    print("Clearing energy prices database...")
    clear_energy_prices_db(conn_prices)
        
    
    print("Clearing cassandra database...")
    clear_cassandra_db(cass_session)


if __name__ == "__main__":
    
    clear_all_db()
