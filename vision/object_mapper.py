# nova_guide/vision/object_mapper.py

"""
A module to map generic object labels from the COCO dataset to
more specific or useful alerts for the Nova-Guide robot.
"""

def map_object_to_alert(label):
    """
    Maps a detected object label to a specific alert message.

    This function can be easily customized to fit your specific needs.
    For example, you could map 'couch' to 'obstacle' or 'stairs' if your
    custom dataset is not yet ready.

    Args:
        label (str): The object label from the YOLO model.

    Returns:
        str: The alert message to be spoken, or None if no alert is needed.
    """
    
    # Priority alerts
    if label == 'person':
        return 'Human'
    if label == 'chair':
        return 'Chair'
    if label == 'door':
        return 'Door'
        
    # General obstacles
    if label in ['couch', 'bed', 'dining table']:
        return 'Obstacle'
        
    # Misidentified objects that you want to specifically announce
    # This is a great place to add custom labels from your future dataset!
    # For example, if you trained a model with 'stairs' as a class, you would add:
    # if label == 'stairs':
    #     return 'Stairs'

    return None
