import requests
from typing import Dict

class TrafficService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def get_traffic_conditions(self, origin: Dict, destination: Dict) -> float:
        """
        Get traffic conditions using Google Maps Distance Matrix API
        Returns a normalized score between 0 and 1
        """
        params = {
            'origins': f"{origin['latitude']},{origin['longitude']}",
            'destinations': f"{destination['latitude']},{destination['longitude']}",
            'key': self.api_key,
            'departure_time': 'now'
        }

        response = requests.get(self.base_url, params=params)
        data = response.json()

        if data['status'] == 'OK':
            duration = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
            base_duration = data['rows'][0]['elements'][0]['duration']['value']
            
            # Calculate traffic score (1 = no traffic, 0 = heavy traffic)
            traffic_score = base_duration / duration if duration > 0 else 1
            return max(0, min(1, traffic_score))
        
        return 0.5  # Default score if API fails 