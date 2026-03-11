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
        "type": "clinic",
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
            place_id = place.get("place_id")
            details = get_place_details(place_id) if place_id else {}

            clinics.append({
                "name": place.get("name"),
                "address": place.get("vicinity") or place.get("formatted_address"),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "rating": place.get("rating"),
                "place_id": place_id,
                "phone_number": details.get("phone_number"),
                "website": details.get("website"),
                "opening_hours": details.get("opening_hours"),
                # "reviews": details.get("reviews"),
                # "google_maps_link": details.get("google_maps_link")
            })

        return clinics
    except Exception as e:
        logger.error(f"Error calling Google Places API: {e}")
        return []


def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,opening_hours,reviews,url",
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        status = data.get("status")
        if status != "OK":
            logger.warning(f"Google Place Details API error: {status} for place_id {place_id}")
            return {}

        result = data.get("result", {})
        opening_hours = result.get("opening_hours", {}).get("weekday_text") if result.get("opening_hours") else None
        google_maps_link = result.get("url") or f"https://www.google.com/maps/place/?q=place_id:{place_id}"

        return {
            "phone_number": result.get("formatted_phone_number"),
            "website": result.get("website"),
            "opening_hours": opening_hours,
            "reviews": result.get("reviews"),
            "google_maps_link": google_maps_link
        }
    except Exception as e:
        logger.error(f"Error calling Google Place Details API: {e}")
        return {}


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
