import pytz

from device_manager_service import generalLogger


def convert_dt_to_utc(dt):
    local = pytz.timezone("Europe/Lisbon")

    try:
        dt = local.localize(dt, is_dst=None)
    except Exception:
        generalLogger.warning(f"Date is not naive. Locale: {dt.tzname()}")
    
    new_dt_utc = dt.astimezone(pytz.utc)

    return new_dt_utc