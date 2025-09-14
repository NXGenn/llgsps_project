from app.core.latency import estimate_transfer_time, LatencyEstimator
from datetime import datetime, timedelta # <-- Add timedelta to this import line

def create_baseline_schedule(all_passes: list, data_demands: list):
    """
    Creates a simple, greedy, conflict-free schedule.

    Args:
        all_passes (list): A list of all possible satellite passes.
        data_demands (list): A list of data transfer demands to be scheduled.

    Returns:
        A tuple of (scheduled contacts, unscheduled demands).
    """
    # Initialize enhanced latency estimator for better accuracy
    latency_estimator = LatencyEstimator()
    
    # Sort passes by their rise time to process them chronologically
    sorted_passes = sorted(all_passes, key=lambda p: p['rise_time'])
    
    # Keep a copy of demands to modify
    remaining_demands = list(data_demands)
    
    scheduled_contacts = []
    # Track the end time of the last scheduled contact (timezone-naive for simple comparison)
    station_busy_until = datetime.min

    for p in sorted_passes:
        # If there are no more demands, we're done
        if not remaining_demands:
            break
        
        # Convert pass rise time to a comparable datetime object (strip timezone info)
        pass_rise_time = datetime.fromisoformat(p['rise_time']).replace(tzinfo=None)

        # Check if the ground station is free
        if pass_rise_time >= station_busy_until:
            # Look for a demand that this pass can satisfy
            for demand in remaining_demands:
                # Use enhanced estimation for better accuracy
                estimation = latency_estimator.estimate_transfer_time_detailed(p, demand['data_mb'])
                
                if estimation and estimation['is_feasible']:
                    # Schedule this contact!
                    contact_end_time = pass_rise_time + timedelta(seconds=estimation['total_required_time_seconds'])
                    
                    scheduled_contact = {
                        "satellite": demand['satellite'],
                        "ground_station": "ISTRAC Bangalore",
                        "demand_mb": demand['data_mb'],
                        "start_time": p['rise_time'],
                        "end_time": contact_end_time.isoformat() + "Z",
                        "duration_seconds": estimation['total_required_time_seconds'],
                        "data_efficiency": estimation.get('data_efficiency', 0.0),
                        "effective_data_rate_mbps": estimation.get('effective_data_rate_mbps', 0.0)
                    }
                    scheduled_contacts.append(scheduled_contact)

                    # Update station busy time and remove the fulfilled demand
                    station_busy_until = contact_end_time
                    remaining_demands.remove(demand)
                    
                    # Move to the next pass, as this one is now allocated
                    break 

    return scheduled_contacts, remaining_demands