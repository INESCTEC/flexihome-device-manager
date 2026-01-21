import os, logging, coloredlogs


generalLogFormat = '%(asctime)s | %(threadName)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d — %(message)s'

generalLogger = logging.getLogger(__name__)
generalLogger.propagate = False


class Config:
    HOST_ENERGYMANAGER = os.environ.get('HOST_ENERGYMANAGER', "http://localhost:8080/api/energy_manager_service")
    HOST_ACCOUNTSERVICE = os.environ.get('HOST_ACCOUNTSERVICE', "http://localhost:8082/api/account")
    
    LOG_LEVEL = logging.getLevelName(os.environ.get('LOG_LEVEL', 'INFO'))

    REQUEST_TIMEOUT_SECONDS = int(os.environ.get('REQUEST_TIMEOUT_SECONDS', '20'))
    SECONDS_BETWEEN_REQUESTS = int(os.environ.get('SECONDS_BETWEEN_REQUESTS', "10"))


coloredlogs.install(
    level=Config.LOG_LEVEL,
    fmt=generalLogFormat,
    datefmt='%Y-%m-%dT%H:%M:%S',
    logger=generalLogger,
    isatty=True,
    )
