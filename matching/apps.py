from django.apps import AppConfig


class MatchingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matching'

    def ready(self):
        # Initialize services
        from .services.traffic_service import TrafficService
        from .services.matching_service import MatchingService
        from .services.navigation_service import NavigationService
