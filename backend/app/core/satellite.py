from skyfield.api import load, EarthSatellite, Topos
from datetime import timedelta, timezone
from pathlib import Path

# Initialize the timescale and ephemeris
ts = load.timescale()
eph = load('de421.bsp')

# Build path to the TLE data directory
TLE_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data/tles/"

def find_satellite_passes(tle_filename: str, ground_station: dict, days: int = 2):
    """
    Calculates the visible passes of a satellite over a ground station for a given number of days.
    """
    # Define the ground station location
    station_location = Topos(
        latitude_degrees=ground_station['latitude'],
        longitude_degrees=ground_station['longitude'],
        elevation_m=ground_station['elevation_m']
    )

    # Load the satellite(s) from the TLE file
    tle_path = TLE_DATA_PATH / tle_filename
    try:
        satellites = load.tle_file(str(tle_path))
        satellite = satellites[0]
    except FileNotFoundError:
        print(f"Error: TLE file not found at {tle_path}")
        return []
    except IndexError:
        print(f"Error: No satellites found in TLE file at {tle_path}")
        return []

    # Define the time window for the search
    t0 = ts.now()
    
    # ---- THIS IS THE FIX ----
    # Convert skyfield time to python datetime, add timedelta, and convert back.
    # The correct method is .utc_datetime() as the error suggested.
    t1 = ts.from_datetime(t0.utc_datetime() + timedelta(days=days))
    # ---- END OF FIX ----

    # Find rise, culmination, and set events
    times, events = satellite.find_events(station_location, t0, t1, altitude_degrees=10.0)
    
    passes = []
    # Group events by pass (rise -> culminate -> set)
    for i, event_type in enumerate(events):
        if event_type == 0:  # This is a rise event
            pass_info = {
                "rise_time": times[i].utc_iso(),
                "culmination_time": times[i+1].utc_iso(),
                "set_time": times[i+2].utc_iso()
            }
            passes.append(pass_info)
    
    return passes