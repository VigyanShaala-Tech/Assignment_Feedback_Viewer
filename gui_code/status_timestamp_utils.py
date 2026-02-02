# utils.py
from datetime import datetime
import pytz

def get_status(remark):
    if not remark:
        return "under review", "gray"

    status_map = {
        "not submitted": ("Not Submitted", "red"),
        "reviewed": ("Accepted", "green"),
        "rejected": ("Improve and Resubmit", "orange"),
        "submitted": ("Under Review", "blue"),
        "pending": ("Under Review", "pink"),
    }

    return status_map.get(
        remark.strip().lower(),
        ("under review", "gray")
    )

def ist_now():
    return datetime.now(
        pytz.timezone("Asia/Kolkata")
    ).replace(tzinfo=None)
