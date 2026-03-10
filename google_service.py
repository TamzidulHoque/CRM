import logging
import requests
from config import API_KEY

logger = logging.getLogger(__name__)

def search_clinics(lat, lng, radius, keyword):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        status = data.get("status")
        if status != "OK":
            logger.error(f"Google Places API error: {status} for radius {radius}")
            return []

        results = data.get("results", [])
        clinics = []
        for place in results:
            location = place.get("geometry", {}).get("location", {})
            clinics.append({
                "name": place.get("name"),
                "address": place.get("vicinity") or place.get("formatted_address"),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "rating": place.get("rating"),
                "place_id": place.get("place_id")
            })

        return clinics
    except Exception as e:
        logger.error(f"Error calling Google Places API: {e}")
        return []


def get_website(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "website",
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        status = data.get("status")
        if status != "OK":
            logger.warning(f"Google Place Details API error: {status} for place_id {place_id}")
            return None
        return data.get("result", {}).get("website")
    except Exception as e:
        logger.error(f"Error calling Google Place Details API: {e}")
        return None
