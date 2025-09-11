from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes

def main():
    print("--- Testing Phase 1 Modules ---")

    # 1. Load ground stations
    stations = load_ground_stations()
    if not stations:
        print("No ground stations loaded. Exiting.")
        return

    # Use the first station for our test
    bangalore_station = stations[0]
    print(f"\nUsing ground station: {bangalore_station['name']}")

    # 2. Find passes for the ISS
    print("Searching for ISS passes over the next 2 days...")
    iss_passes = find_satellite_passes('iss.txt', bangalore_station)

    if not iss_passes:
        print("No upcoming passes found.")
        return

    print(f"\nFound {len(iss_passes)} passes:")
    for i, p in enumerate(iss_passes):
        print(f"\n--- Pass {i+1} ---")
        print(f"  Rise:       {p['rise_time']}")
        print(f"  Culminate:  {p['culmination_time']}")
        print(f"  Set:        {p['set_time']}")

if __name__ == "__main__":
    main()