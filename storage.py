import json
import os
from datetime import datetime, timedelta, timezone

FILE_NAME = "registered_clinics.json"
EMAIL_LOG_FILE = "email_log.json"


def load_registered():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r") as f:
        return json.load(f)


def save_registered(clinic_name):
    data = load_registered()
    data.append(clinic_name)

    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)


def _load_email_log():
    if not os.path.exists(EMAIL_LOG_FILE):
        return {}

    with open(EMAIL_LOG_FILE, "r") as f:
        return json.load(f)


def _save_email_log(log):
    with open(EMAIL_LOG_FILE, "w") as f:
        json.dump(log, f, indent=4)


def can_send_email_to_clinic(clinic_name, cooldown_days=30):
    """
    Return True if we are allowed to send an email to this clinic now.
    Enforces a cooldown based on the last time we sent to this clinic.
    """
    log = _load_email_log()
    last_sent_str = log.get(clinic_name)
    if not last_sent_str:
        return True

    try:
        last_sent = datetime.fromisoformat(last_sent_str)
    except Exception:
        # If we cannot parse, allow sending and overwrite.
        return True

    now = datetime.now(timezone.utc)
    return now - last_sent >= timedelta(days=cooldown_days)


def mark_email_sent_to_clinic(clinic_name):
    log = _load_email_log()
    log[clinic_name] = datetime.now(timezone.utc).isoformat()
    _save_email_log(log)

