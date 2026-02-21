import re
import requests
from config import *
from google_service import search_clinics, get_website
from email_service import send_registration_email
from storage import load_registered, save_registered
from user_location import get_current_location


def extract_email(url):
    try:
        response = requests.get(url, timeout=10)
        emails = re.findall(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            response.text
        )
        return list(set(emails))
    except:
        return []


def run_system(user_lat, user_lng):

    registered = load_registered()
    radius = SEARCH_RADIUS_START

    while radius <= SEARCH_RADIUS_MAX:

        print(f"\nSearching radius: {radius/1000} km")

        clinics = search_clinics(user_lat, user_lng, radius)

        for clinic in clinics:

            name = clinic["name"]

            if name in registered:
                print("Registered clinic found:", name)
                print("Notify user to choose clinic")
                return

            website = get_website(clinic["place_id"])

            if website:
                emails = extract_email(website)

                for email in emails:
                    print("Sending registration to:", name)
                    send_registration_email(email, name)
                    save_registered(name)

        radius += SEARCH_RADIUS_STEP

    print("No registered clinic found in range.")


# Example: Dhaka coordinates
# run_system(23.8103, 90.4125,"Dermal fillers")

lat, lng = get_current_location()

if lat and lng:
    run_system(lat, lng)
else:
    print("Location detection failed.")

