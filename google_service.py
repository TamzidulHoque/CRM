import requests
from config import API_KEY

def search_clinics(lat, lng, radius, keyword):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("results", [])


def get_website(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "website",
        "key": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("result", {}).get("website")
