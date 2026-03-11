from user_location import get_current_location

# delegate business logic to a separate module
from operations import search_and_notify, run_system


if __name__ == "__main__":
    # Example: Dhaka coordinates
    # run_system(23.8103, 90.4125, "Dermal fillers")

    lat, lng = get_current_location()