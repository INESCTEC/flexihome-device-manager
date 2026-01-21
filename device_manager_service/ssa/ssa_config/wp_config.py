import os

class WPConfig:

    # GA Config #

    # GENERIC_ADAPTER_URL = os.environ.get("WHIRLPOOL_GA_URL", "http://localhost:9090")
    GENERIC_ADAPTER_GLOBAL_URL = os.environ.get("WHIRLPOOL_GA_GLOBAL_URL", "http://localhost:9090")
    GENERIC_ADAPTER_PT_URL = os.environ.get("WHIRLPOOL_GA_PT_URL", "http://localhost:9090")

    # Service store credentials
    USER_EMAIL = os.environ.get("WHIRLPOOL_SERVICE_USER_EMAIL", "vasco.m.campos@inesctec.pt")
    USER_PASSWORD = os.environ.get("WHIRLPOOL_SERVICE_USER_PASSWORD", "Abc123456")


    # Service Register Variables #
    
    # Service
    WP_SERVICE_ID = os.environ.get("WP_SERVICE_ID", "450455")
    WP_SERVICE_PRIMARY_URL = os.environ.get("WP_SERVICE_PRIMARY_URL", "https://ke.interconnectproject.eu/rest")
    INESCTEC_WP_SERVICE_ID = os.environ.get("INESCTEC_WP_SERVICE_ID", "838561")
    INESCTEC_WP_SERVICE_PRIMARY_URL = os.environ.get("INESCTEC_WP_SERVICE_PRIMARY_URL", "https://ke-pt.interconnectproject.eu/rest")
    
    # KB Smart Connector
    KB_ASSET_ID = os.environ.get("WHIRLPOOL_KB_ASSET_ID", "wp-kb-local")
    KB_REACT_ASSET_ID = os.environ.get("WHIRLPOOL_REACT_KB_ASSET_ID", "wp-react-kb-local")
    KB_NAME = os.environ.get("WHIRLPOOL_KB_NAME", "INESC SSA for Whirlpool requests")
    KB_DESCRIPTION = os.environ.get("WHIRLPOOL_KB_DESCRIPTION", "INESC TEC HEMS KB smart connector for Whirlpool")
    ADAPTER_OPTIONAL_KB = os.environ.get("WHIRLPOOL_ADAPTER_OPTIONAL_KB", "https://ke-pt.interconnectproject.eu/rest")

    # Knowledge Interactions
    APPLIANCES_ASK_KI_NAME = os.environ.get("APPLIANCES_ASK_KI_NAME", "wp-appliances-ask-ki-local")
    REGISTER_ASK_KI_NAME = os.environ.get("REGISTER_ASK_KI_NAME", "wp-register-ask-ki-local")
    PP_REACT_KI_NAME = os.environ.get("PP_REACT_KI_NAME", "wp-pp-react-ki-local")
    DELAY_POST_KI_NAME = os.environ.get("DELAY_POST_KI_NAME", "wp-delay-react-ki-local")

    PLAYER_ID = os.environ.get("PLAYER_ID", "PT-Uxs9e")


    # Interaction Customization Variables #

    # WP_GET_APPLIANCES_RESPONSE_TIMEOUT_SECONDS = int(os.environ.get("WP_GET_APPLIANCES_RESPONSE_TIMEOUT_SECONDS", "10"))
    # WP_GET_APPLIANCES_SELF_HEAL_TRIES = int(os.environ.get("WP_GET_APPLIANCES_SELF_HEAL_TRIES", "1"))

    # WP_REGISTER_APPLIANCES_RESPONSE_TIMEOUT_SECONDS = int(os.environ.get("WP_REGISTER_APPLIANCES_RESPONSE_TIMEOUT_SECONDS", "10"))
    # WP_REGISTER_APPLIANCES_SELF_HEAL_TRIES = int(os.environ.get("WP_REGISTER_APPLIANCES_SELF_HEAL_TRIES", "1"))

    # WP_DELAYED_START_RESPONSE_TIMEOUT_SECONDS = int(os.environ.get("WP_DELAYED_START_RESPONSE_TIMEOUT_SECONDS", "10"))
    # WP_DELAYED_START_SELF_HEAL_TRIES = int(os.environ.get("WP_DELAYED_START_SELF_HEAL_TRIES", "1"))
    
    HANDLE_DEBUG_FLAG = True if os.environ.get("WP_HANDLE_DEBUG_FLAG", "false").lower() == "true" else False
    minutes_in_three_days = str(60 * 24 * 3)
    WP_POWER_PROFILE_SELF_HEAL_FLAG = True if os.environ.get("WP_POWER_PROFILE_SELF_HEAL_FLAG", "true").lower() == "true" else False
    WP_TIME_INTERVAL_TO_REFRESH_KB_MINUTES = int(os.environ.get("WP_TIME_INTERVAL_TO_REFRESH_KB_MINUTES", minutes_in_three_days))
    
    SECONDS_UNTIL_RECONNECT_TRY = int(os.environ.get("WP_HANDLE_SECONDS_UNTIL_RECONNECT_TRY", "10"))
    ASK_POST_RESPONSE_TIMEOUT_SECONDS = int(os.environ.get("ASK_POST_RESPONSE_TIMEOUT_SECONDS", "15"))
    ASK_POST_SELF_HEAL_TRIES = int(os.environ.get("ASK_POST_SELF_HEAL_TRIES", "1"))
