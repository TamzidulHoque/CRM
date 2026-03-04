"""Core business operations for clinic discovery and outreach.

This module contains the high-level functions used by the CLI script and
any other consumer; keeping the workflow here makes the implementation
cleaner and easier to test.  The previous monolithic logic lived in
``main.py`` and contained various helper functions; those have been
extracted.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional

import requests

from config import SEARCH_RADIUS_MAX, SEARCH_RADIUS_START, SEARCH_RADIUS_STEP
from google_service import get_website, search_clinics
from email_service import send_registration_email
from storage import (
    can_send_email_to_clinic,
    load_registered,
    mark_email_sent_to_clinic,
    save_registered,
    record_clinic,
)


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def extract_emails(url: str) -> List[str]:
    """Retrieve the given URL and return a list of email addresses.

    Network failures and parsing errors are swallowed and result in an
    empty list.  The regex simply matches ``foo@domain`` patterns; callers
    are responsible for a final sanity check.
    """

    try:
        resp = requests.get(url, timeout=10)
        return list(set(re.findall(EMAIL_REGEX, resp.text)))
    except Exception:  # any network/IO problem
        return []


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def run_system(
    user_lat: float,
    user_lng: float,
    keywords: str,
    max_radius_m: Optional[int] = None,
) -> Optional[str]:
    """Search for clinics around ``user_lat``/``user_lng`` and send invites.

    ``keywords`` is forwarded to Google Places.  ``max_radius_m`` if
    provided bounds the search radius; otherwise ``SEARCH_RADIUS_MAX`` is
    used.  The function returns the name of a *registered* clinic if one is
    encountered while expanding the radius.  ``None`` indicates no such
    clinic was found.
    """

    registered = load_registered()
    radius = SEARCH_RADIUS_START
    upper = max_radius_m if max_radius_m is not None else SEARCH_RADIUS_MAX

    while radius <= upper:
        clinics = search_clinics(user_lat, user_lng, radius, keywords)

        for clinic in clinics:
            name = clinic.get("name")
            record_clinic(name)

            if name in registered:
                return name

            website = get_website(clinic.get("place_id"))
            if not website:
                continue

            for email in extract_emails(website):
                if not EMAIL_REGEX.fullmatch(email):
                    continue

                if not can_send_email_to_clinic(name):
                    continue

                send_registration_email(email, name)
                save_registered(name)
                mark_email_sent_to_clinic(name, email)

        radius += SEARCH_RADIUS_STEP

    return None


def search_and_notify(user_lat: float, user_lng: float, keywords: str) -> None:
    """Wrapper used by the command‑line driver to print progress."""

    found = run_system(user_lat, user_lng, keywords)
    if found:
        print("Registered clinic found:", found)
    else:
        print("No registered clinic found in range.")
