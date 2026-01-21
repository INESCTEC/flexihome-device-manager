import os

class CybergridConfig:

    # PT PILOT - Service Store Config
    PT_PILOT_GENERIC_ADAPTER_URL = os.environ.get("PT_PILOT_GENERIC_ADAPTER_URL", "http://localhost:9090")
    # PT_PILOT_GENERIC_ADAPTER_URL = os.environ.get("PT_PILOT_GENERIC_ADAPTER_URL", "http://ga.default.svc.cluster.local:9090")
    
    USER_EMAIL = os.environ.get("USER_EMAIL", "ruben.m.queiros@inesctec.pt")
    USER_PASSWORD = os.environ.get("USER_PASSWORD", "IC123456*")

    # Cybergrid service config
    CYBERGRID_SERVICE_ID = os.environ.get("CYBERGRID_SERVICE_ID", "767123")
    CYBERGRID_SERVICE_PRIMARY_URL = os.environ.get("CYBERGRID_SERVICE_PRIMARY_URL", "https://ke-pt.interconnectproject.eu/rest")

    # Cybergrid Reactive KB Config
    REACTIVE_KB_NAME = os.environ.get("REACTIVE_KB_NAME", "INESC TEC reactive KB for CyberGrid")
    REACTIVE_KB_DESCRIPTION = os.environ.get("REACTIVE_KB_DESCRIPTION", "KB for receiving setpoints from CyberGrid")
    REACTIVE_KB_ASSET_ID = os.environ.get("REACTIVE_KB_ASSET_ID", "cybergrid-reactive-kb")

    SETPOINT_KI_NAME = os.environ.get("SETPOINT_KI_NAME", "setpoint-ki")

    minutes_in_three_days = str(60 * 24 * 3)
    REACTIVE_KB_REFRESH_TIMER_MINUTES = int(os.environ.get("REACTIVE_KB_REFRESH_TIMER_MINUTES", minutes_in_three_days))

    REACTIVE_SECONDS_UNTIL_RECONNECT_TRY = int(os.environ.get("REACTIVE_SECONDS_UNTIL_RECONNECT_TRY", "10"))

    # Cybergrid Proactive KB Config
    PROACTIVE_KB_NAME = os.environ.get("PROACTIVE_KB_NAME", "INESC TEC proactive KB for CyberGrid")
    PROACTIVE_KB_DESCRIPTION = os.environ.get("PROACTIVE_KB_DESCRIPTION", "KB for sending the baseline to CyberGrid")
    PROACTIVE_KB_ASSET_ID = os.environ.get("PROACTIVE_KB_ASSET_ID", "cybergrid-proactive-kb")

    BASELINE_KI_NAME = os.environ.get("BASELINE_KI_NAME", "baseline-ki")
    UPPER_LIMIT_KI_NAME = os.environ.get("UPPER_LIMIT_KI_NAME", "upper-limit-ki")
    LOWER_LIMIT_KI_NAME = os.environ.get("LOWER_LIMIT_KI_NAME", "lower-limit-ki")
    SETPOINT_POST_KI_NAME = os.environ.get("SETPOINT_POST_KI_NAME", "setpoint-post-ki")


    # OV PILOT - Service Store Config
    OV_PILOT_GENERIC_ADAPTER_URL = os.environ.get("OV_PILOT_GENERIC_ADAPTER_URL", "http://localhost:9089")

    OV_KB_NAME = os.environ.get("OV_KB_NAME", "INESC TEC OV Pilot KB for CyberGrid")
    OV_KB_DESCRIPTION = os.environ.get("OV_KB_DESCRIPTION", "KB for sending active power to CyberGrid")
    OV_KB_ASSET_ID = os.environ.get("OV_KB_ASSET_ID", "cybergrid-ov-proactive-kb")

    ACTIVE_POWER_KI_NAME = os.environ.get("ACTIVE_POWER_KI_NAME", "active-power-ki")


    # Interaction options
    ASK_POST_RESPONSE_TIMEOUT_SECONDS = int(os.environ.get("ASK_POST_RESPONSE_TIMEOUT_SECONDS", "5"))
    ASK_POST_SELF_HEAL_TRIES = int(os.environ.get("ASK_POST_SELF_HEAL_TRIES", "1"))