# navigation/indoor.py

def go_to_location(location_name, coords):
    """
    Simulates the robot moving to a specified indoor location.
    
    Args:
        location_name (str): The name of the destination (e.g., "kitchen").
        coords (list): A list of [x, y] coordinates.
    """
    print(f"🧭 [IndoorNav] Simulating movement to {location_name} at coordinates {coords}.")
    # In the next phase, this will be replaced with real motor control commands
    # and obstacle avoidance logic.
