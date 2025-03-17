from math import radians, sin, cos, sqrt, atan2

def calculate_distance(point1: dict, point2: dict) -> float:
    """
    Calculate distance between two points using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers

    lat1 = radians(point1['latitude'])
    lon1 = radians(point1['longitude'])
    lat2 = radians(point2['latitude'])
    lon2 = radians(point2['longitude'])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance 