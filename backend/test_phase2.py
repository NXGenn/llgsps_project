from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.scheduling.baseline import create_baseline_schedule

def main():
    print("--- Testing Phase 2 Modules ---")
    
    # 1. Get all available passes (from Phase 1)
    stations = load_ground_stations()
    if not stations:
        return
    bangalore_station = stations[0]
    iss_passes = find_satellite_passes('iss.txt', bangalore_station, days=2)
    print(f"Found {len(iss_passes)} total potential ISS passes.")

    # 2. Define some mock data demands
    mock_demands = [
        {"satellite": "ISS", "data_mb": 450},
        {"satellite": "ISS", "data_mb": 600},
        {"satellite": "ISS", "data_mb": 300},
    ]
    print(f"Attempting to schedule {len(mock_demands)} data demands.")

    # 3. Create the baseline schedule
    schedule, unscheduled = create_baseline_schedule(iss_passes, mock_demands)

    # 4. Print the results
    print("\n--- Baseline Schedule ---")
    if not schedule:
        print("No contacts could be scheduled.")
    else:
        for i, contact in enumerate(schedule):
            print(f"\n--- Contact {i+1} ---")
            print(f"  Satellite: {contact['satellite']}")
            print(f"  Demand:    {contact['demand_mb']} MB")
            print(f"  Start:     {contact['start_time']}")
            print(f"  End:       {contact['end_time']}")

    if unscheduled:
        print("\n--- Unscheduled Demands ---")
        for demand in unscheduled:
            print(f"  Could not schedule {demand['data_mb']} MB for {demand['satellite']}")

if __name__ == "__main__":
    main()