import os

class BSHConfig:
    
    # GA Config #

    # GENERIC_ADAPTER_URL = os.environ.get("BSH_GA_URL", "http://localhost:9090")
    GENERIC_ADAPTER_URL = os.environ.get("BSH_GA_URL", "http://ic-demo.hesilab.nl:9090")

    # Service store credentials
    USER_EMAIL = os.environ.get("BSH_SERVICE_USER_EMAIL", "vasco.m.campos@inesctec.pt")
    USER_PASSWORD = os.environ.get("BSH_SERVICE_USER_PASSWORD", "Abc123456")


    # Service Register Variables #
    
    # Service
    BSH_SERVICE_ID = os.environ.get("BSH_REACTIVE_SERVICE_ID", "883224")
    BSH_SERVICE_PRIMARY_URL = os.environ.get("BSH_REACTIVE_SERVICE_PRIMARY_URL", "https://ke-pt.interconnectproject.eu/rest")
    INESCTEC_BSH_SERVICE_ID = os.environ.get("INESCTEC_BSH_SERVICE_ID", "839166")
    INESCTEC_BSH_SERVICE_PRIMARY_URL = os.environ.get("INESCTEC_BSH_SERVICE_PRIMARY_URL", "https://ke-pt.interconnectproject.eu/rest")
    
    # KB Smart Connector
    KB_ASSET_ID = os.environ.get("BSH_KB_ASSET_ID", "BSH-kb-local")
    KB_REACT_ASSET_ID = os.environ.get("BSH_REACT_KB_ASSET_ID", "BSH-react-kb-local")
    KB_NAME = os.environ.get("BSH_KB_NAME", "INESC SSA for BSH requests")
    KB_DESCRIPTION = os.environ.get("BSH_KB_DESCRIPTION", "INESC TEC HEMS KB smart connector for BSH")

    # Knowledge Interactions
    PP_REACT_KI_NAME = os.environ.get("BSH_PP_KI_NAME", "BSH-pp-react-ki-local")
    DELAY_POST_KI_NAME = os.environ.get("BSH_DELAY_KI_NAME", "BSH-delay-post-ki-local")
    DEVICE_METADATA_ASK_KI_NAME = os.environ.get("DEVICE_METADATA_ASK_KI_NAME", "BSH-device-metadata-ask-ki-local")
    CONNECTION_STATE_REACT_KI_NAME = os.environ.get("BSH_CONNECTION_STATE_REACT_KI_NAME", "connection-state-react-ki-local")


    # Interaction Customization Variables #
    
    minutes_in_three_days = str(60 * 24 * 3)
    BSH_POWER_PROFILE_SELF_HEAL_FLAG = True if os.environ.get("BSH_POWER_PROFILE_SELF_HEAL_FLAG", "true").lower() == "true" else False
    BSH_TIME_INTERVAL_TO_REFRESH_KB_MINUTES = int(os.environ.get("BSH_TIME_INTERVAL_TO_REFRESH_KB_MINUTES", minutes_in_three_days))
    HANDLE_DEBUG_FLAG = True if os.environ.get("BSH_HANDLE_DEBUG_FLAG", "false").lower() == "true" else False

    REACTIVE_WAIT_TIMEOUT_SECONDS = int(os.environ.get("BSH_REACTIVE_WAIT_TIMEOUT_SECONDS", "10"))
    REACTIVE_SELF_HEAL_FLAG = True if os.environ.get("BSH_REACTIVE_SELF_HEAL_FLAG", "true").lower() == "true" else False
    REACTIVE_DELETE_KB_FLAG = True if os.environ.get("BSH_REACTIVE_DELETE_KB_FLAG", "true").lower() == "true" else False
    REACTIVE_SELF_HEAL_TRIES = int(os.environ.get("BSH_REACTIVE_SELF_HEAL_TRIES", "1"))

    BSH_DELAYED_START_RESPONSE_WAIT_TIMEOUT_SECONDS = int(os.environ.get("BSH_DELAYED_START_RESPONSE_WAIT_TIMEOUT_SECONDS", "10"))
    BSH_DELAYED_START_SELF_HEAL_FLAG = True if os.environ.get("BSH_DELAYED_START_SELF_HEAL_FLAG", "true").lower() == "true" else False
    BSH_DELAYED_START_DELETE_KB_FLAG = True if os.environ.get("BSH_DELAYED_START_DELETE_KB_FLAG", "true").lower() == "true" else False
    BSH_DELAYED_START_SELF_HEAL_TRIES = int(os.environ.get("BSH_DELAYED_START_SELF_HEAL_TRIES", "1"))

    ASK_DEVICE_METADATA_TIMEOUT = int(os.environ.get("ASK_DEVICE_METADATA_TIMEOUT", "10"))
    ASK_DEVICE_METADATA_SELF_HEAL_TRIES = int(os.environ.get("ASK_DEVICE_METADATA_SELF_HEAL_TRIES", "1"))
    
    SECONDS_UNTIL_RECONNECT_TRY = int(os.environ.get("BSH_HANDLE_SECONDS_UNTIL_RECONNECT_TRY", "10"))
