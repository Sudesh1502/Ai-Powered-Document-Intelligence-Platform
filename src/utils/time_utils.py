from datetime import datetime, timezone, timedelta

def get_ist_now():
    """Returns the current time explicitly forced to Indian Standard Time (UTC+5:30)"""
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
