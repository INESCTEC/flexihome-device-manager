import os
import logging
import datetime


class Config:
    
    
    ############################### DATABASE ###############################
    
    # ENERGY MANAGER
    DATABASE_IP = os.environ.get('DATABASE_IP', '127.0.0.1')
    DATABASE_PORT = os.environ.get('DATABASE_PORT', '5432')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'mysecretpassword')
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_IP}:{DATABASE_PORT}/energy_manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AUTH_DATABASE_USER = os.environ.get('AUTH_DATABASE_USER', 'postgres')
    AUTH_DATABASE_PASSWORD = os.environ.get('AUTH_DATABASE_PASSWORD', 'mysecretpassword')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        # "max_overflow": int(os.environ.get("SQLALCHEMY_MAX_OVERFLOW", "5")),
        # "pool_size": int(os.environ.get("SQLALCHEMY_POOL_SIZE", "10")),
        "pool_pre_ping": True if os.environ.get("SQLALCHEMY_POOL_PRE_PING", "True").lower() == "true" else False,
        "pool_logging_name": os.environ.get("SQLALCHEMY_POOL_LOGGING_NAME", "pool_log"),
        # "isolation_level": SQLALCHEMY_ISOLATION_LEVEL
        'connect_args': {
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 30,
            "keepalives_count": 5,
        }
    }
    SQLALCHEMY_BINDS = {
        'energy_manager': f'postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_IP}:{DATABASE_PORT}/energy_manager',
    }
    
    # JWT TOKEN MANAGEMENT
    AUTH_DATABASE_USER = os.environ.get('AUTH_DATABASE_USER', 'postgres')
    AUTH_DATABASE_PASSWORD = os.environ.get('AUTH_DATABASE_PASSWORD', 'mysecretpassword')
    
    JWT_SIGN_ALGORITHM = 'HS512'
    JWT_EXPIRATION_TIME_SECONDS = 14 * 24 * 60 * 60
    JWT_SIGN_KEY = os.environ.get('JWT_SIGN_KEY', 'f797b720a53f8e9c71d33700f2a703acea28985dd427369a3f55f48ba171998e408b44c072c1d9dfb06192aa6808c8a9e28b68dbe842d0c1473405fc298f31708ad12168bcdeb642ba619866ae1c0a49fa4fa248818535105ec7931901589de6b4f316273994003db830f23331b12c9da51415d479ead7729bb30c7df54aaf78')

    
    ############################ LOGS & METRICS ############################
    
    LOG_LEVEL = logging.getLevelName(os.environ.get('LOG_LEVEL', 'INFO'))
    LOG_FORMAT = logging.getLevelName(os.environ.get('LOG_FORMAT', 'text'))
    OC_AGENT_ENDPOINT = os.environ.get('OC_AGENT_ENDPOINT', '127.0.0.1:6831')
    
    
    ################################ KAFKA ################################

    KAFKA_BOOTSTRAP_SERVERS  = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_NOTIFICATION = os.getenv('KAFKA_NOTIFICATION_TOPIC', "hems.notifications")

    KAFKA_RECONNECT_SLEEP_SECONDS = 5
    KAFKA_CONNECTION_ATTEMPTS = 3

    
    ####################### GENERIC SERVICE CONFIGS #######################
    
    TEST_MODE = False if os.environ.get("TEST_MODE", "false").lower() == "false" else True
    DEMO_MODE = False if os.environ.get("DEMO_MODE", "false").lower() == "false" else True
    REQUEST_TIMEOUT_SECONDS = int(os.environ.get('REQUEST_TIMEOUT_SECONDS', '20'))
    MAINTENANCE_MODE = False if os.environ.get("MAINTENANCE_MODE", "false").lower() == "false" else True
    ACTIVATE_DEFAULT_DATA = False if os.environ.get("ACTIVATE_DEFAULT_DATA", "true").lower() == "false" else True

    ######################## OPTMIZATION PARAMETERS ########################

    TIMESTAMP_FORMAT      = os.environ.get( 'TIMESTAMP_FORMAT',      str("%Y-%m-%dT%H:%M:%SZ") )
    TIMESTAMP_WITH_TZ_FORMAT = os.environ.get( 'TIMESTAMP_WITH_TZ_FORMAT', "%Y-%m-%dT%H:%M:%S%z" )
    DATE_FORMAT           = os.environ.get('DATE_FORMAT',            "%Y-%m-%d")
    COUNTRY               = os.environ.get( 'COUNTRY',               'Portugal' )
    CONSUMER_TYPE         = os.environ.get( 'CONSUMER_TYPE',         'yearly' )
    PRICE_TYPE            = os.environ.get( 'PRICE_TYPE'   ,         'both' )
    SLOT_MIN              = int(os.environ.get( 'SLOT_MIN',          "5" ))
    DELIVERY_TIME         = int(os.environ.get( 'DELIVERY_TIME',     "15" ))
    PERIODS               = int(os.environ.get( 'PERIODS',           int(24 * 60 / DELIVERY_TIME) ))
    GEO_ID                = int(os.environ.get( 'GEO_ID',            "1" ))
    DECIMAL               = int(os.environ.get( 'DECIMAL',           "6" ))
    FORECAST_TYPE         = os.environ.get( 'FORECAST_TYPE',         ['consumption'] )
    FLEXIBILITY_GATE_TIMESTAMP = os.environ.get( 'FLEXIBILITY_GATE_TIMESTAMP', (datetime.datetime.now()).replace(hour=23,minute=30,second=0,microsecond=0) )
    SCHEDULE_GATE_TIMESTAMP    = os.environ.get( 'SCHEDULE_GATE_TIMESTAMP',    (datetime.datetime.now()).replace(hour=23,minute=30,second=0,microsecond=0) )


    ##################### EXTERNAL SERVICES ENDPOINTS #####################

    if TEST_MODE:
        HOST_ACCOUNTSERVICE       = os.environ.get('HOST_ACCOUNTSERVICE',       "http://localhost:8082/api/account")
        HOST_ENERGYPRICESSERVICE  = os.environ.get('HOST_ENERGYPRICESSERVICE',  "http://localhost:8086/api/energy-prices")
        HOST_FORECASTSERVICE      = os.environ.get('HOST_FORECASTSERVICE',      "http://localhost:8085/api/forecast")
        HOST_DEVICEMANAGERSERVICE = os.environ.get('HOST_DEVICEMANAGERSERVICE', "http://localhost:8084/api/device")
        HOST_STATISTICSERVICE     = os.environ.get('HOST_STATISTICSERVICE',     "http://localhost:8087/api/statistics")
        HOST_SENTINEL             = os.environ.get('HOST_SENTINEL',             "http://vcpes08.inesctec.pt:8000/data/inesctec")
        HOST_AGGREGATOR           = os.environ.get('HOST_AGGREGATOR',           "http://localhost:8079/api/aggregator")
        HOST_ENERGYMANAGER        = os.environ.get('HOST_ENERGYMANAGER',        "http://localhost:8080/api/energy_manager_service")
    else:
        HOST_ACCOUNTSERVICE       = os.environ.get('HOST_ACCOUNTSERVICE',       "http://account-manager.default.svc.cluster.local:8080/api/account")
        HOST_ENERGYPRICESSERVICE  = os.environ.get('HOST_ENERGYPRICESSERVICE',  "http://energy-prices.default.svc.cluster.local:8080/api/energy-prices")
        HOST_FORECASTSERVICE      = os.environ.get('HOST_FORECASTSERVICE',      "http://forecast-rest-api.default.svc.cluster.local:8080/api/forecast")
        HOST_DEVICEMANAGERSERVICE = os.environ.get('HOST_DEVICEMANAGERSERVICE', "http://device-manager.default.svc.cluster.local:8080/api/device")
        HOST_STATISTICSERVICE     = os.environ.get('HOST_STATISTICSERVICE',     "http://statistics-manager.default.svc.cluster.local:8080/api/statistics")
        HOST_SENTINEL             = os.environ.get('HOST_SENTINEL',             "http://vcpes08.inesctec.pt:8000/data/inesctec")
        HOST_AGGREGATOR           = os.environ.get('HOST_AGGREGATOR',           "http://localhost:8079/api/aggregator")
        # HOST_ENERGYMANAGER        = os.environ.get('HOST_ENERGYMANAGER',        "http://energy-manager.default.svc.cluster.local:8080/api/energy_manager_service")
        HOST_ENERGYMANAGER        = os.environ.get('HOST_ENERGYMANAGER',        "http://localhost:8080/api/energy_manager_service")

    
    ####################### SENTINEL AUTHENTICATION #######################
    
    SENTINEL_TOKEN   = os.environ.get('SENTINEL_TOKEN', "token d4acfad2e46b05a71eecbe8fb2b92101a095c47b")
    X_CSRFTOKEN      = os.environ.get('X_CSRFTOKEN',    "tM35bpL8mJK5NMRMPJbLQpBvtZKHLkAtLISzoC0xo5YW3OJ7G5G1vYEd3HAXOHDr")


    ####################### SSA #######################

    CYBERGRID_THREAD = True if os.environ.get("CYBERGRID_THREAD", "true").lower() == "true" else False
    BASELINE_DAYS_AHEAD = int(os.environ.get("BASELINE_DAYS_AHEAD", "1"))


    ####################### INFLUX CONNECTION #######################

    if TEST_MODE:
        INFLUX_URL = os.environ.get('INFLUX_URL', 'http://localhost:9002')
        INFLUX_TOKEN = os.environ.get('INFLUX_STAGING_TOKEN', 'test-token')
    else:
        INFLUX_URL = os.environ.get('INFLUX_URL', 'http://influxdb-influxdb2.default.svc.cluster.local:80')
        INFLUX_TOKEN = os.environ.get('INFLUX_TOKEN', 'prod-token')
    
    INFLUX_ORG = os.environ.get('INFLUX_ORG', 'influxdata')
    INFLUX_BUCKET = os.environ.get('INFLUX_BUCKET', 'interconnect-eot-meters')
