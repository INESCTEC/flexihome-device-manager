import os


class Config:
    ACCOUNT_MANAGER_ENDPOINT = os.environ.get("ACCOUNT_MANAGER_ENDPOINT_TEST", "http://localhost:8082/api/account")
    DEVICE_MANAGER_ENDPOINT = os.environ.get("DEVICE_MANAGER_ENDPOINT_TEST", "http://localhost:8084/api/device")
    FORECAST_ENDPOINT_TEST = os.environ.get('FORECAST_ENDPOINT_TEST', "http://localhost:8085")


    DATABASE_IP = os.environ.get('DATABASE_IP', '127.0.0.1')
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT', '5432'))
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'mysecretpassword')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'energy_manager')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_IP}:{DATABASE_PORT}/energy_manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }
    SQLALCHEMY_BINDS = {
        'energy_manager': f'postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_IP}:{DATABASE_PORT}/energy_manager',
    }