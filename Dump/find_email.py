import requests
import re
import json

API_KEY = "AIzaSyAUMPkWSv-SxdMIADMiqQezQxXlrxnQ3hA"


def search_clinics(location, keyword):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{keyword} in {location}",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("results", [])


def get_place_website(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("result", {}).get("website")


def extract_email(url):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)
        return list(set(emails))
    except:
        return []


clinics = search_clinics("Manchester", "Dermal Filler")

output = []

for clinic in clinics:
    name = clinic.get("name")
    place_id = clinic.get("place_id")

    website = get_place_website(place_id)

    if website:
        emails = extract_email(website)

        if emails:
            output.append({
                "name": name,
                "emails": emails
            })

            print(f"Saved: {name}")


# Save JSON
with open("clinic_emails.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print("\n✅ Only clinic names + emails saved to clinic_emails.json")
