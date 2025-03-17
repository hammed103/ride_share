import googlemaps
from typing import Dict, List

class NavigationService:
    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key="AIzaSyCf32K4RI5TiysGJ1RbAIl7_Y5bAgPUNuU")

    def get_optimal_route(
        self, 
        origin: Dict[str, float], 
        destination: Dict[str, float],
        waypoints: List[Dict[str, float]] = None
    ) -> Dict:
        """
        Get optimal route using Google Maps Directions API
        Returns route information including waypoints, distance, and duration
        """
        # Convert origin and destination to the format expected by the library
        origin_str = f"{origin['latitude']},{origin['longitude']}"
        destination_str = f"{destination['latitude']},{destination['longitude']}"
        
        # Prepare waypoints if provided
        waypoints_list = None
        if waypoints:
            waypoints_list = [
                f"{point['latitude']},{point['longitude']}" 
                for point in waypoints
            ]
        
        # Get directions using the client library
        directions_result = self.client.directions(
            origin=origin_str,
            destination=destination_str,
            waypoints=waypoints_list,
            alternatives=True,
            mode="driving"
        )
        
        return directions_result 