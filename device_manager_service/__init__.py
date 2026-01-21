from flask_sqlalchemy import SQLAlchemy
import connexion
import logging, coloredlogs, traceback
from pythonjsonlogger import jsonlogger
from prometheus_flask_exporter import ConnexionPrometheusMetrics
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace import config_integration, samplers
from opencensus.ext.ocagent.trace_exporter import TraceExporter
from datetime import datetime, timezone
from time import sleep

from hems_auth.auth import Auth

from device_manager_service import encoder
from device_manager_service.config import Config

from device_manager_service.ssa.ssa_classes.whirlpool_ssa import WhirlpoolSSA
from device_manager_service.ssa.ssa_config.wp_config import WPConfig

from device_manager_service.ssa.ssa_classes.bsh_ssa import BSHSSA
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig

from device_manager_service.ssa.ssa_classes.userkb_ssa import UserkbSSA
from device_manager_service.ssa.ssa_config.userkb_config import UserkbConfig


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        """
        Override this method to implement custom logic for adding fields.
        """
        for field in self._required_fields:
            if field in self.rename_fields:
                log_record[self.rename_fields[field]
                           ] = record.__dict__.get(field)
            else:
                log_record[field] = record.__dict__.get(field)
        log_record.update(self.static_fields)
        log_record.update(message_dict)
        jsonlogger.merge_record_extra(
            record, log_record, reserved=self._skip_fields)

        if self.timestamp:
            key = self.timestamp if type(
                self.timestamp) == str else 'timestamp'
            log_record[key] = datetime.fromtimestamp(
                record.created, tz=timezone.utc).isoformat(timespec='milliseconds')


# Configure opencensus tracing integrations (plugins)
config_integration.trace_integrations(['logging'])
config_integration.trace_integrations(['sqlalchemy'])
config_integration.trace_integrations(['requests'])

# Setup Flask app
connexionApp = connexion.App(__name__,
                             specification_dir='./openapi/',
                             options={"swagger_ui": False})
connexionApp.app.json_encoder = encoder.JSONEncoder

app = connexionApp.app
app.config.from_object(Config)

# Setup Flask SQLAlchemy
db = SQLAlchemy(app)

# Setup logger
if Config.LOG_FORMAT == "json":
    generalLogFormat = '%(asctime)s | %(name)s | %(threadName)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d — %(message)s'
    appLogFormat = '%(asctime)s | %(name)s | %(threadName)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d — X-Correlation-ID=%(X-Correlation-ID)s — traceId=%(traceId)s — spanId=%(spanId)s — %(message)s'

    generalFormatter = CustomJsonFormatter(generalLogFormat, timestamp=True)
    generalLogHandler = logging.StreamHandler()
    generalLogHandler.setFormatter(generalFormatter)

    # Set log config for all modules
    logging.basicConfig(level=logging.INFO, handlers=[generalLogHandler])

    # Set log config for our app
    logger = logging.getLogger(__name__ + "_logger")

    appFormatter = CustomJsonFormatter(appLogFormat, timestamp=True)
    appLogHandler = logging.StreamHandler()
    appLogHandler.setFormatter(appFormatter)

    logger.setLevel(Config.LOG_LEVEL)
    logger.addHandler(appLogHandler)
else:
    # Format for all modules except our app (e.g., Flask logs, Waitress logs, etc.)
    generalLogFormat = '%(asctime)s | %(name)s | %(threadName)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d — %(message)s'
    # Format for our app, which includes the X-Correlation-ID string as required
    appLogFormat = '%(asctime)s | %(name)s | %(threadName)s | %(levelname)s | %(module)s.%(funcName)s:%(lineno)d — X-Correlation-ID=%(X-Correlation-ID)s — traceId=%(traceId)s — spanId=%(spanId)s — %(message)s'

    # Set log config for our app
    logger = logging.getLogger(__name__ + "_logger")

    coloredlogs.install(
        level=Config.LOG_LEVEL,
        fmt=appLogFormat,
        datefmt='%Y-%m-%dT%H:%M:%S',
        logger=logger,
        isatty=True,
        )


# Do not propagate (app log handler -> root handler)
# Without this, the logs of our app are printed twice
logger.propagate = False

generalLogger = logging.getLogger(__name__)
generalLogger.propagate = False
generalLogger.setLevel(Config.LOG_LEVEL)

coloredlogs.install(
    level=Config.LOG_LEVEL,
    fmt=generalLogFormat,
    datefmt='%Y-%m-%dT%H:%M:%S',
    logger=generalLogger,
    isatty=True,
)

# Kafka logger configuration
kafka_logger = logging.getLogger("kafka")  # NOTE: We can detail which kafka module we want to log, by using its like, p. e. 'kafka.conn' or 'kafka.coordinator'
kafka_logger.propagate = False
coloredlogs.install(
    level=Config.KAFKA_LOG_LEVEL,
    fmt=generalLogFormat,
    datefmt='%Y-%m-%dT%H:%M:%S',
    logger=kafka_logger,
    isatty=True
)

# Sqlalchemy logger configuration
sqlalchemy_engine_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_engine_logger.propagate = False
coloredlogs.install(
    level=Config.SQLALCHEMY_LOG_LEVEL,
    fmt=generalLogFormat,
    datefmt='%Y-%m-%dT%H:%M:%S',
    logger=sqlalchemy_engine_logger,
    isatty=True
)


# Setup Prometheus metrics
metrics = ConnexionPrometheusMetrics(connexionApp, group_by='url_rule')

metrics.info('app_info', 'Device Manager Service', version='1.0.0')

# OpenCencus tracing
exporter = TraceExporter(
    service_name='Device Manager Service',
    endpoint=Config.OC_AGENT_ENDPOINT,
)

sampler = samplers.AlwaysOnSampler()

middleware = FlaskMiddleware(app, exporter=exporter, sampler=sampler)


auth = Auth(
    jwt_sign_key=Config.JWT_SIGN_KEY, 
    jwt_sign_algorithm=Config.JWT_SIGN_ALGORITHM,
    DATABASE_IP=Config.DATABASE_IP, 
    DATABASE_PORT=Config.DATABASE_PORT,
    DATABASE_USER=Config.AUTH_DATABASE_USER, 
    DATABASE_PASSWORD=Config.AUTH_DATABASE_PASSWORD
)


# ---------------------- SSA instances ---------------------- #


# # WHIRLPOOL SSA
# whirlpool_ssa = WhirlpoolSSA(
#     ga_url=WPConfig.GENERIC_ADAPTER_URL,
#     ss_email=WPConfig.USER_EMAIL,
#     ss_password=WPConfig.USER_PASSWORD,
#     kb_name=WPConfig.KB_NAME,
#     kb_description=WPConfig.KB_DESCRIPTION,
#     asset_id=WPConfig.KB_ASSET_ID,
#     logger=generalLogger
# )


# WHIRLPOOL SSA
setup_complete = False
while not setup_complete:
    try:
        whirlpool_proactive_ssa = WhirlpoolSSA(
            ga_url=WPConfig.GENERIC_ADAPTER_GLOBAL_URL,
            ss_email=WPConfig.USER_EMAIL,
            ss_password=WPConfig.USER_PASSWORD,
            kb_name=WPConfig.KB_NAME,
            kb_description=WPConfig.KB_DESCRIPTION,
            asset_id=WPConfig.KB_ASSET_ID,
            logger=generalLogger
        )
        setup_complete = True
    except Exception as e:
        traceback.print_exc()
        generalLogger.error(repr(e))

        # Wait x seconds before trying again
        generalLogger.warning(
            f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
            "before trying the SSA setup again..."
        )
        sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)


# WHIRLPOOL SSA
setup_complete = False
while not setup_complete:
    try:
        whirlpool_reactive_ssa = WhirlpoolSSA(
            ga_url=WPConfig.GENERIC_ADAPTER_PT_URL,
            ss_email=WPConfig.USER_EMAIL,
            ss_password=WPConfig.USER_PASSWORD,
            kb_name=WPConfig.KB_NAME,
            kb_description=WPConfig.KB_DESCRIPTION,
            asset_id=WPConfig.KB_ASSET_ID,
            logger=generalLogger
        )
        setup_complete = True
    except Exception as e:
        traceback.print_exc()
        generalLogger.error(repr(e))

        # Wait x seconds before trying again
        generalLogger.warning(
            f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
            "before trying the SSA setup again..."
        )
        sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)


# # BSH SSA
# bsh_ssa = BSHSSA(
#     ga_url=BSHConfig.GENERIC_ADAPTER_URL,
#     ss_email=BSHConfig.USER_EMAIL,
#     ss_password=BSHConfig.USER_PASSWORD,
#     kb_name=BSHConfig.KB_NAME,
#     kb_description=BSHConfig.KB_DESCRIPTION,
#     asset_id=BSHConfig.KB_ASSET_ID,
#     logger=generalLogger
# )


# BSH SSA
setup_complete = False
while not setup_complete:
    try:
        bsh_proactive_ssa = BSHSSA(
            ga_url=BSHConfig.GENERIC_ADAPTER_URL,
            ss_email=BSHConfig.USER_EMAIL,
            ss_password=BSHConfig.USER_PASSWORD,
            kb_name=BSHConfig.KB_NAME,
            kb_description=BSHConfig.KB_DESCRIPTION,
            asset_id=BSHConfig.KB_ASSET_ID,
            logger=generalLogger
        )
        setup_complete = True
    except Exception as e:
        traceback.print_exc()
        generalLogger.error(repr(e))

        # Wait x seconds before trying again
        generalLogger.warning(
            f"Waiting {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
            "before trying the SSA setup again..."
        )
        sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)


# # Userkb SSA
# userkb_ssa = UserkbSSA(
#     ga_url=UserkbConfig.GENERIC_ADAPTER_URL,
#     ss_email=UserkbConfig.USER_EMAIL,
#     ss_password=UserkbConfig.USER_PASSWORD,
#     kb_name=UserkbConfig.KB_NAME,
#     kb_description=UserkbConfig.KB_DESCRIPTION,
#     asset_id=UserkbConfig.KB_ASSET_ID,
#     logger=generalLogger
# )


# Userkb SSA
setup_complete = False
while not setup_complete:
    try:
        userkb_ssa = UserkbSSA(
            ga_url=UserkbConfig.GENERIC_ADAPTER_URL,
            ss_email=UserkbConfig.USER_EMAIL,
            ss_password=UserkbConfig.USER_PASSWORD,
            kb_name=UserkbConfig.KB_NAME,
            kb_description=UserkbConfig.KB_DESCRIPTION,
            asset_id=UserkbConfig.KB_ASSET_ID,
            logger=generalLogger
        )
        setup_complete = True
    except Exception as e:
        traceback.print_exc()
        generalLogger.error(repr(e))

        # Wait x seconds before trying again
        generalLogger.warning(
            f"Waiting {UserkbConfig.SSA_TIMEOUT_SECONDS} seconds " \
            "before trying the SSA setup again..."
        )
        sleep(UserkbConfig.SSA_TIMEOUT_SECONDS)
