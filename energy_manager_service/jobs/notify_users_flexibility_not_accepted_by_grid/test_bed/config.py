import os


class Config:
    DATABASE_IP = os.environ.get('DATABASE_IP', '127.0.0.1')
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT', '5432'))
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'mysecretpassword')
