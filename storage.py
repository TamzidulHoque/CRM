import json
import os

FILE_NAME = "registered_clinics.json"

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
