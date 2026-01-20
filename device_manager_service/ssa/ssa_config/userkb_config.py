import os

class UserkbConfig:
    
    # GA Config #

    # GENERIC_ADAPTER_URL = os.environ.get("BSH_GA_URL", "http://localhost:9090")
    GENERIC_ADAPTER_URL = os.environ.get("BSH_GA_URL", "http://ic-demo.hesilab.nl:9090")

    # Service store credentials
    USER_EMAIL = os.environ.get("BSH_SERVICE_USER_EMAIL", "vasco.m.campos@inesctec.pt")
    USER_PASSWORD = os.environ.get("BSH_SERVICE_USER_PASSWORD", "Abc123456")
    
    
    # Service Register Variables #

    SPINE_ADAPTER_SERVICE_ID = os.environ.get("SPINE_ADAPTER_SERVICE_ID", "883224")
    SPINE_ADAPTER_PRIMARY_URL = os.environ.get("SPINE_ADAPTER_PRIMARY_URL", "https://ke-pt.interconnectproject.eu/rest")

    KB_NAME = os.environ.get("USERKB_KB_NAME", "HEMS User KB")
    KB_DESCRIPTION = os.environ.get("USERKB_KB_DESCRIPTION", "HEMS User Knowledge Base to store user preferences regarding the HEMS")
    KB_ASSET_ID = os.environ.get("USERKB_KB_ASSET_ID", "hems-userkb-kb")

    DEVICE_ACCESS_KI_NAME = os.environ.get("DEVICE_ACCESS_KI_NAME", "userkb-device-access-ki")


    SSA_TIMEOUT_SECONDS = int(os.environ.get("USERKB_SSA_TIMEOUT_SECONDS", "10"))
