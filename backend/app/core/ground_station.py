import json
from pathlib import Path

# Build the path to the data file
DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data/ground_stations.json"

def load_ground_stations():
    """Loads ground station data from the JSON file."""
    try:
        with open(DATA_PATH, 'r') as f:
            stations = json.load(f)
        print(f"Successfully loaded {len(stations)} ground station(s).")
        return stations
    except FileNotFoundError:
        print(f"Error: Ground station file not found at {DATA_PATH}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {DATA_PATH}")
        return []