import re
import requests

from config import SEARCH_RADIUS_MAX, SEARCH_RADIUS_START, SEARCH_RADIUS_STEP
from google_service import get_website, search_clinics
from email_service import send_registration_email
from storage import (
    can_send_email_to_clinic,
    load_registered,
    mark_email_sent_to_clinic,
    save_registered,
)
from user_location import get_current_location


def extract_email(url):
    try:
        response = requests.get(url, timeout=10)
        emails = re.findall(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            response.text,
        )
        return list(set(emails))
    except Exception:
        return []


def run_system(user_lat, user_lng, keywords, max_radius_m=None):
    """
    Run search from user's lat/lng for `keywords`.

    If `max_radius_m` is provided (meters) the search will expand from
    SEARCH_RADIUS_START up to that value instead of using the global
    SEARCH_RADIUS_MAX. This allows the backend/frontend to control the
    selected search range.
    """
    registered = load_registered()
    radius = SEARCH_RADIUS_START

    # determine upper bound (meters)
    upper = max_radius_m if max_radius_m is not None else SEARCH_RADIUS_MAX

    while radius <= upper:
        print(f"\nSearching radius: {radius/1000} km")

        clinics = search_clinics(user_lat, user_lng, radius, keywords)
        print(f"Found {len(clinics)} clinics in this radius")

        for clinic in clinics:
            name = clinic["name"]

            if name in registered:
                print("Registered clinic found:", name)
                print("Notify user to choose clinic")
                return

            website = get_website(clinic["place_id"])

            if website:
                print(f"  Website found: {website}")
                emails = extract_email(website)
                print(f"  Emails extracted: {emails}")

                for email in emails:
                    # basic sanity check: must match email regex exactly
                    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
                        print(f"    skipping invalid email: {email}")
                        continue

                    if can_send_email_to_clinic(name):
                        print("Sending registration to:", name, "at", email)
                        try:
                            send_registration_email(email, name)
                        except Exception as exc:
                            print("    failed to send to", email, "-", exc)
                            continue
                        # save_registered(name)
                        mark_email_sent_to_clinic(name)
                    else:
                        print("Skipping email to", name, "- last email was sent less than 30 days ago")
            else:
                print(f"  No website found for {name}")

        radius += SEARCH_RADIUS_STEP

    print("No registered clinic found in range.")


if __name__ == "__main__":
    # Example: Dhaka coordinates
    # run_system(23.8103, 90.4125, "Dermal fillers")

    lat, lng = get_current_location()

    if lat and lng:
        print(f"Current location: {lat}, {lng}")
        run_system(lat, lng, "Dermal fillers")
    else:
        print("Location detection failed.")

