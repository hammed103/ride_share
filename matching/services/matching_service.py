from typing import List, Dict
from ..models import Driver, Passenger, Ride
from .traffic_service import TrafficService
from .distance_calculator import calculate_distance
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('matching')

class MatchingService:
    def __init__(self, traffic_service: TrafficService):
        self.traffic_service = traffic_service
        self.weights = {
            'distance': 0.25,
            'traffic': 0.2,
            'rating': 0.2,
            'preferences': 0.25,
            'fairness': 0.1  # New weight for fair distribution
        }

    def calculate_preference_score(self, driver_prefs: Dict, passenger_prefs: Dict) -> float:
        """Calculate matching score based on preferences"""
        matches = sum(1 for k in passenger_prefs if k in driver_prefs and driver_prefs[k] == passenger_prefs[k])
        total = len(passenger_prefs)
        return matches / total if total > 0 else 0

    def calculate_distance_score(self, driver_location: Dict, pickup_location: Dict) -> float:
        """Calculate score based on distance (closer is better)"""
        try:
            distance = calculate_distance(driver_location, pickup_location)
            # Normalize: 1 for very close (0 km), 0 for far (20+ km)
            return max(0, 1 - distance / 20)
        except Exception as e:
            logger.error(f"Error calculating distance score: {str(e)}")
            return 0.5  # Default middle score if calculation fails

    def calculate_fairness_score(self, driver: Driver) -> float:
        """Calculate fairness score based on recent rides"""
        recent_rides = Ride.objects.filter(
            driver=driver,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Normalize score (0 rides = 1.0, 10+ rides = 0.0)
        MAX_DAILY_RIDES = 10
        return max(0, min(1, 1 - (recent_rides / MAX_DAILY_RIDES)))

    def find_best_match(self, passenger: Passenger) -> List[Driver]:
        """Find best matching drivers for a passenger"""
        available_drivers = Driver.objects.filter(available=True).exclude(location=None)
        
        if not available_drivers:
            return []
            
        pickup_location = passenger.pickup_location
        passenger_prefs = passenger.preferences
        
        scored_drivers = []
        
        for driver in available_drivers:
            try:
                # Calculate distance score
                distance_score = self.calculate_distance_score(driver.location, pickup_location)
                
                # Calculate traffic score
                traffic_score = self.traffic_service.get_traffic_conditions(
                    driver.location, pickup_location
                )
                
                # Calculate preference score
                preference_score = self.calculate_preference_score(
                    driver.preferences, passenger_prefs
                )
                
                # Calculate rating score (normalize to 0-1)
                rating_score = driver.rating / 5.0
                
                # Calculate fairness score (drivers with fewer rides get priority)
                recent_rides = Ride.objects.filter(
                    driver=driver, 
                    created_at__gte=timezone.now() - timedelta(days=1)
                ).count()
                fairness_score = max(0, 1 - (recent_rides / 10))  # 0 rides = 1, 10+ rides = 0
                
                # Calculate total score
                total_score = (
                    self.weights['distance'] * distance_score +
                    self.weights['traffic'] * traffic_score +
                    self.weights['rating'] * rating_score +
                    self.weights['preferences'] * preference_score +
                    self.weights['fairness'] * fairness_score
                )
                
                scored_drivers.append((driver, total_score))
                
            except Exception as e:
                logger.error(f"Error scoring driver {driver.id}: {str(e)}")
                continue
        
        # Sort by score (highest first) and return just the drivers
        scored_drivers.sort(key=lambda x: x[1], reverse=True)
        return [driver for driver, _ in scored_drivers] 