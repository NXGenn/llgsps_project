from app.core.ground_station import load_ground_stations
from app.core.satellite import find_satellite_passes
from app.scheduling.baseline import create_baseline_schedule
from app.scheduling.optimizer import create_optimized_schedule
import time

def main():
    print("======================================================")
    print("= LLGSPS Scheduling System Demo                    =")
    print("======================================================")
    print("This demo will compare a traditional scheduling model against our advanced optimizer.")
    print("-" * 54)

    # --- Shared Setup ---
    stations = load_ground_stations()
    if not stations: return
    bangalore_station = stations[0]
    
    print("\nStep 1: Calculating all potential satellite passes for the next 24 hours...")
    iss_passes = find_satellite_passes('iss.txt', bangalore_station, days=1)
    
    mock_demands = [
        {"satellite": "ISS", "data_mb": 150}, # Small, can fit anywhere
        {"satellite": "ISS", "data_mb": 1200},# Very large, needs a long pass
        {"satellite": "ISS", "data_mb": 200}, # Small
        {"satellite": "ISS", "data_mb": 500}, # Medium
    ]
    total_possible_data = sum(d['data_mb'] for d in mock_demands)
    print(f"Found {len(iss_passes)} potential passes.")
    print(f"Attempting to schedule {len(mock_demands)} demands totaling {total_possible_data} MB.\n")
    time.sleep(2) # Pause for dramatic effect

    # --- 1. Run the Traditional (Baseline) Scheduler ---
    print("--- 2. Running Traditional (Greedy) Scheduler ---")
    print("This model takes the first available pass for each demand, which can be inefficient.")
    time.sleep(1)
    baseline_schedule, baseline_unscheduled = create_baseline_schedule(iss_passes, mock_demands)
    baseline_total_data = sum(c['demand_mb'] for c in baseline_schedule)
    print(f"\n  Result: Scheduled {len(baseline_schedule)} contacts.")
    print(f"  Total Data Scheduled: {baseline_total_data} / {total_possible_data} MB")
    if baseline_unscheduled:
        print(f"  Unscheduled demands: {[d['data_mb'] for d in baseline_unscheduled]} MB")


    # --- 2. Run the Optimized Scheduler ---
    print("\n\n--- 3. Running Our Advanced Optimizer ---")
    print("Our model analyzes all possibilities to find the mathematically optimal solution.")
    time.sleep(1)
    opt_schedule, opt_unscheduled = create_optimized_schedule(iss_passes, mock_demands)
    opt_total_data = sum(c['demand_mb'] for c in opt_schedule)
    print(f"\n  Result: Scheduled {len(opt_schedule)} contacts.")
    print(f"  Total Data Scheduled: {opt_total_data} / {total_possible_data} MB")
    if opt_unscheduled:
        print(f"  Unscheduled demands: {[d['data_mb'] for d in opt_unscheduled]} MB")
    
    print("\n\n======================================================")
    print("=                     DEMO COMPLETE                  =")
    print("======================================================")
    if (opt_total_data > baseline_total_data):
        print(f"✅ The optimizer scheduled an additional {opt_total_data - baseline_total_data} MB of data!")
        print("This proves the value of our intelligent scheduling approach.")
    else:
        print("Both schedulers found the same solution for this scenario.")


if __name__ == "__main__":
    main()