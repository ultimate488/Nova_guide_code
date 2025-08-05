# navigation/outdoor.py

from geopy.geocoders import Nominatim

# We'll use a mock Nominatim for now to avoid external API calls during simulation.
class MockNominatim:
    def __init__(self, *args, **kwargs):
        pass
    def geocode(self, place):
        print(f"🌐 [OutdoorNav] Geocoding '{place}'...")
        # Return a mock location for a well-known place in your area
        if "pharmacy" in place.lower():
            # Mock coordinates for a pharmacy near your current location (Ettumanoor, Kerala)
            return type('MockLocation', (object,), {'latitude': 9.689, 'longitude': 76.495})()
        if "supermarket" in place.lower():
            return type('MockLocation', (object,), {'latitude': 9.68, 'longitude': 76.5})()
        return None

def get_coords(place):
    """
    Gets the GPS coordinates for a given place name.
    
    Args:
        place (str): The name of the place (e.g., "nearest pharmacy").
        
    Returns:
        tuple: A tuple of (latitude, longitude), or None if not found.
    """
    geolocator = MockNominatim(user_agent="nova-guide")
    location = geolocator.geocode(place)
    if location:
        return (location.latitude, location.longitude)
    return None

def get_current_coords():
    """
    Mocks the current GPS coordinates of the robot.
    (Simulating Ettumanoor, Kerala, India).
    
    Returns:
        tuple: A tuple of (latitude, longitude).
    """
    return (9.684, 76.488)

def show_route(start_coords, end_coords):
    """
    Simulates getting and providing a route from a start to end point.
    
    Args:
        start_coords (tuple): The starting GPS coordinates.
        end_coords (tuple): The destination GPS coordinates.
    """
    print(f"🗺️ [OutdoorNav] Planning route from {start_coords} to {end_coords}.")
    # In a real-world scenario, this would call a routing API.
    # For now, we just print the action.
