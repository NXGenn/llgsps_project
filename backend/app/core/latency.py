from datetime import datetime, timezone

def estimate_transfer_time(pass_info: dict, data_demand_mb: float, data_rate_mbps: float = 150):
    """
    Estimates the time required for a data transfer and checks if it fits in the pass.

    Args:
        pass_info (dict): A dictionary containing 'rise_time', 'set_time'.
        data_demand_mb (float): The amount of data to transfer in Megabytes.
        data_rate_mbps (float): The downlink data rate in Megabits per second.

    Returns:
        A dictionary with feasibility and details, or None if input is invalid.
    """
    try:
        # Convert ISO format strings to datetime objects
        rise_time = datetime.fromisoformat(pass_info['rise_time'])
        set_time = datetime.fromisoformat(pass_info['set_time'])

        # Calculate the total duration of the pass in seconds
        pass_duration_seconds = (set_time - rise_time).total_seconds()

        # Calculate required transfer time in seconds (Note: MB vs Mbps)
        # Data in Megabits = data_demand_mb * 8
        required_time_seconds = (data_demand_mb * 8) / data_rate_mbps

        # Check if the transfer is possible within the pass duration
        is_feasible = pass_duration_seconds >= required_time_seconds

        return {
            "is_feasible": is_feasible,
            "required_time_seconds": round(required_time_seconds, 2),
            "pass_duration_seconds": round(pass_duration_seconds, 2)
        }
    except (KeyError, TypeError):
        return None