import requests


def get_current_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()

        lat = data["lat"]
        lng = data["lon"]

        # print("Detected location:", data["city"], data["country"])
        return lat, lng

    except Exception:
        print("Could not detect location")
        return None, None


if __name__ == "__main__":
    lat, lng = get_current_location()
    print(lat, lng)
