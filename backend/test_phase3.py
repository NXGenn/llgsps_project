from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.scheduling.optimizer import create_optimized_schedule

def main():
    print("--- Testing Phase 3: Optimizer Module ---")
    
    # 1. Get all available passes (from Phase 1)
    stations = load_ground_stations()
    if not stations: return
    bangalore_station = stations[0]
    iss_passes = find_satellite_passes('iss.txt', bangalore_station, days=2)
    print(f"Found {len(iss_passes)} total potential ISS passes.")

    # 2. Define mock data demands, including some that might conflict
    mock_demands = [
        {"satellite": "ISS", "data_mb": 450}, # Fits in most passes
        {"satellite": "ISS", "data_mb": 800}, # Large, requires a long pass
        {"satellite": "ISS", "data_mb": 300}, # Small, flexible
        {"satellite": "ISS", "data_mb": 500}, 
    ]
    print(f"Attempting to schedule {len(mock_demands)} data demands to maximize throughput.")

    # 3. Create the optimized schedule
    schedule, unscheduled = create_optimized_schedule(iss_passes, mock_demands)

    # 4. Print the results
    print("\n--- Optimized Schedule ---")
    total_data = 0
    if not schedule:
        print("No contacts could be scheduled.")
    else:
        for i, contact in enumerate(schedule):
            total_data += contact['demand_mb']
            print(f"\n--- Contact {i+1} ---")
            print(f"  Satellite: {contact['satellite']} | Demand: {contact['demand_mb']} MB")
            print(f"  Start: {contact['start_time']} | End: {contact['end_time']}")
    
    print(f"\nTotal data scheduled: {total_data} MB")

    if unscheduled:
        print("\n--- Unscheduled Demands ---")
        for demand in unscheduled:
            print(f"  Could not schedule {demand['data_mb']} MB for {demand['satellite']}")

if __name__ == "__main__":
    main()