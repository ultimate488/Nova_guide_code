# memory/learn.py

import json
import os

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'commands.json')

def save_room(name, coords):
    """
    Saves a new room name and its coordinates to the commands.json file.
    
    Args:
        name (str): The name of the room (e.g., "hall").
        coords (list): A list of two floats representing the [x, y] coordinates.
    """
    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            rooms = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle cases where the file doesn't exist or is empty
        rooms = {}
        
    rooms[name] = coords
    
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(rooms, f, indent=2)
    print(f"✅ [Memory] Saved room '{name}' at coordinates {coords}.")

def load_rooms():
    """
    Loads all saved room names and their coordinates from the commands.json file.
    
    Returns:
        dict: A dictionary of room names mapped to their coordinates.
    """
    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return an empty dictionary if the file doesn't exist or is empty
        print("⚠️ [Memory] No room data found. Starting with an empty map.")
        return {}
