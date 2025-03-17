from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated

from .models import Driver, Passenger, Ride, RideRequest
from .serializers import (
    DriverSerializer, 
    PassengerSerializer,
    RideSerializer,
    RideMatchRequestSerializer,
    RouteRequestSerializer,
    RideRequestSerializer
)
from .services.matching_service import MatchingService
from .services.navigation_service import NavigationService
from .services.traffic_service import TrafficService

# Initialize services
traffic_service = TrafficService(api_key=settings.GOOGLE_MAPS_API_KEY)
matching_service = MatchingService(traffic_service=traffic_service)
navigation_service = NavigationService(api_key=settings.GOOGLE_MAPS_API_KEY)

class DriverViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing drivers
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    
    def get_queryset(self):
        # If user is staff, return all drivers
        if self.request.user.is_staff:
            return Driver.objects.all()
        # Otherwise, return only the driver associated with the current user
        return Driver.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's driver profile"""
        try:
            driver = Driver.objects.get(user=request.user)
            serializer = self.get_serializer(driver)
            return Response(serializer.data)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update the current user's driver profile"""
        try:
            driver = Driver.objects.get(user=request.user)
            serializer = self.get_serializer(driver, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def toggle_availability(self, request):
        """Toggle the driver's availability status"""
        try:
            driver = Driver.objects.get(user=request.user)
            driver.available = not driver.available
            driver.save()
            return Response({
                'available': driver.available,
                'message': f'Availability set to {driver.available}'
            })
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """Update the driver's current location"""
        try:
            driver = Driver.objects.get(user=request.user)
            location = request.data.get('location')
            if not location or 'latitude' not in location or 'longitude' not in location:
                return Response(
                    {'error': 'Invalid location data'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            driver.location = location
            driver.save()
            return Response({
                'location': driver.location,
                'message': 'Location updated successfully'
            })
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PassengerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing passengers
    """
    queryset = Passenger.objects.all()
    serializer_class = PassengerSerializer
    
    def get_queryset(self):
        # If user is staff, return all passengers
        if self.request.user.is_staff:
            return Passenger.objects.all()
        # Otherwise, return only the passenger associated with the current user
        return Passenger.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's passenger profile"""
        try:
            passenger = Passenger.objects.get(user=request.user)
            serializer = self.get_serializer(passenger)
            return Response(serializer.data)
        except Passenger.DoesNotExist:
            return Response(
                {'error': 'Passenger profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update the current user's passenger profile"""
        try:
            passenger = Passenger.objects.get(user=request.user)
            serializer = self.get_serializer(passenger, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Passenger.DoesNotExist:
            return Response(
                {'error': 'Passenger profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class RideViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing rides
    """
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    @swagger_auto_schema(
        operation_description="Update ride status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
                )
            }
        ),
        responses={
            200: openapi.Response('Status updated successfully'),
            400: openapi.Response('Invalid status')
        }
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        ride = self.get_object()
        new_status = request.data.get('status')
        if new_status in [s[0] for s in Ride._meta.get_field('status').choices]:
            ride.status = new_status
            ride.save()
            return Response({'status': 'ride status updated'})
        return Response(
            {'error': 'Invalid status'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class RideMatchingViewSet(viewsets.ViewSet):
    """
    API endpoint for matching passengers with drivers
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Find best matching drivers for a passenger",
        request_body=RideMatchRequestSerializer,
        responses={
            200: openapi.Response(
                'Matched drivers found',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'ride': openapi.Schema(type=openapi.TYPE_OBJECT, ref='#/components/schemas/Ride'),
                        'ride_requests': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT, ref='#/components/schemas/RideRequest')
                        )
                    }
                )
            ),
            404: openapi.Response('No drivers found or passenger not found'),
            400: openapi.Response('Invalid request data')
        }
    )
    def create(self, request):
        serializer = RideMatchRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Get the passenger associated with the current user
                passenger_id = serializer.validated_data.get('passenger_id')
                
                # If passenger_id is provided, check if it belongs to the current user
                if passenger_id:
                    try:
                        passenger = Passenger.objects.get(id=passenger_id)
                        # Check if the passenger belongs to the current user
                        if passenger.user != request.user and not request.user.is_staff:
                            return Response(
                                {'error': 'You do not have permission to request rides for this passenger'}, 
                                status=status.HTTP_403_FORBIDDEN
                            )
                    except Passenger.DoesNotExist:
                        return Response(
                            {'error': 'Passenger not found'}, 
                            status=status.HTTP_404_NOT_FOUND
                        )
                else:
                    # If no passenger_id provided, use the passenger associated with the current user
                    try:
                        passenger = Passenger.objects.get(user=request.user)
                    except Passenger.DoesNotExist:
                        return Response(
                            {'error': 'No passenger profile found for current user'}, 
                            status=status.HTTP_404_NOT_FOUND
                        )
                
                # Update passenger's pickup_location and destination
                passenger.pickup_location = serializer.validated_data['pickup_location']
                passenger.destination = serializer.validated_data['destination']
                passenger.save()
                
                # Check if there are available drivers
                available_drivers = Driver.objects.filter(available=True)
                if not available_drivers.exists():
                    return Response(
                        {'error': 'No available drivers found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Check if any driver has a location set
                drivers_with_location = available_drivers.exclude(location=None)
                if not drivers_with_location.exists():
                    return Response(
                        {'error': 'No drivers with location information available'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Find best matching drivers
                try:
                    matched_drivers = matching_service.find_best_match(passenger)
                    
                    if matched_drivers:
                        # Create a ride with the first matched driver (required by model)
                        # but it will remain PENDING until a driver accepts
                        ride = Ride.objects.create(
                            driver=matched_drivers[0],  # Assign first driver temporarily
                            passenger=passenger,
                            pickup_location=serializer.validated_data['pickup_location'],
                            destination=serializer.validated_data['destination'],
                            status='PENDING'
                        )
                        
                        # Create ride requests for top 3 drivers (or fewer if not enough matches)
                        max_requests = min(3, len(matched_drivers))
                        ride_requests = []
                        
                        for i in range(max_requests):
                            ride_request = RideRequest.objects.create(
                                ride=ride,
                                driver=matched_drivers[i],
                                status='PENDING'
                            )
                            ride_requests.append(ride_request)
                        
                        # Here you would typically send notifications to drivers
                        # This could be implemented with WebSockets, push notifications, etc.
                        
                        return Response({
                            'ride': RideSerializer(ride).data,
                            'ride_requests': RideRequestSerializer(ride_requests, many=True).data
                        })
                    return Response(
                        {'error': 'No suitable drivers found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger('matching')
                    logger.error(f"Error in matching service: {str(e)}")
                    return Response(
                        {'error': f'Error in matching service: {str(e)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except Exception as e:
                import logging
                logger = logging.getLogger('matching')
                logger.error(f"Error in ride matching: {str(e)}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NavigationViewSet(viewsets.ViewSet):
    """
    API endpoint for route navigation and travel time estimation
    """
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description="Get optimal route between two points with estimated travel time",
        request_body=RouteRequestSerializer,
        responses={
            200: openapi.Response(
                'Route details',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'routes': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'distance': openapi.Schema(type=openapi.TYPE_OBJECT),
                                    'duration': openapi.Schema(type=openapi.TYPE_OBJECT),
                                    'steps': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                    ),
                                    'polyline': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                        'best_route_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'estimated_arrival_time': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response('Invalid request data')
        }
    )
    def create(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Get route information from navigation service
            route_data = navigation_service.get_optimal_route(
                origin=serializer.validated_data['origin'],
                destination=serializer.validated_data['destination'],
                waypoints=serializer.validated_data.get('waypoints')
            )
            
            # Process the response to add more useful information
            if route_data and len(route_data) > 0:
                # Find the best route (usually the first one)
                best_route_index = 0
                
                # Calculate estimated arrival time
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if 'legs' in route_data[best_route_index] and route_data[best_route_index]['legs']:
                    # Sum up the duration of all legs in the route
                    total_duration_seconds = sum(
                        leg.get('duration', {}).get('value', 0) 
                        for leg in route_data[best_route_index]['legs']
                    )
                    estimated_arrival = now + timedelta(seconds=total_duration_seconds)
                    
                    # Calculate total distance in meters
                    total_distance_meters = sum(
                        leg.get('distance', {}).get('value', 0) 
                        for leg in route_data[best_route_index]['legs']
                    )
                    
                    # Format distance text
                    if total_distance_meters >= 1000:
                        distance_text = f"{total_distance_meters/1000:.1f} km"
                    else:
                        distance_text = f"{total_distance_meters} m"
                    
                    # Format duration text
                    hours, remainder = divmod(total_duration_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration_text = ""
                    if hours > 0:
                        duration_text += f"{int(hours)} hour{'s' if hours > 1 else ''} "
                    if minutes > 0 or (hours > 0 and minutes == 0):
                        duration_text += f"{int(minutes)} min{'s' if minutes > 1 else ''}"
                    if hours == 0 and minutes == 0:
                        duration_text = f"{int(seconds)} sec{'s' if seconds > 1 else ''}"
                    
                    # Format the response
                    response_data = {
                        'routes': route_data,
                        'best_route_index': best_route_index,
                        'estimated_arrival_time': estimated_arrival.isoformat(),
                        'summary': {
                            'total_distance': {
                                'text': distance_text,
                                'value': total_distance_meters
                            },
                            'total_duration': {
                                'text': duration_text.strip(),
                                'value': total_duration_seconds
                            }
                        }
                    }
                    
                    return Response(response_data)
            
            # Return the raw data if we couldn't process it
            return Response(route_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Get estimated travel time between two points",
        request_body=RouteRequestSerializer,
        responses={
            200: openapi.Response(
                'Travel time estimation',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'duration': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'text': openapi.Schema(type=openapi.TYPE_STRING),
                                'value': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        ),
                        'distance': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'text': openapi.Schema(type=openapi.TYPE_STRING),
                                'value': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        ),
                        'estimated_arrival_time': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response('Invalid request data')
        }
    )
    @action(detail=False, methods=['post'])
    def estimate_travel_time(self, request):
        """Get estimated travel time between two points"""
        serializer = RouteRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Get route information from navigation service
            route_data = navigation_service.get_optimal_route(
                origin=serializer.validated_data['origin'],
                destination=serializer.validated_data['destination'],
                waypoints=serializer.validated_data.get('waypoints')
            )
            
            # Extract just the duration and distance information
            if route_data and len(route_data) > 0 and 'legs' in route_data[0] and route_data[0]['legs']:
                # Calculate total duration and distance
                total_duration_seconds = sum(
                    leg.get('duration', {}).get('value', 0) 
                    for leg in route_data[0]['legs']
                )
                total_distance_meters = sum(
                    leg.get('distance', {}).get('value', 0) 
                    for leg in route_data[0]['legs']
                )
                
                # Format duration text
                hours, remainder = divmod(total_duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_text = ""
                if hours > 0:
                    duration_text += f"{int(hours)} hour{'s' if hours > 1 else ''} "
                if minutes > 0 or (hours > 0 and minutes == 0):
                    duration_text += f"{int(minutes)} min{'s' if minutes > 1 else ''}"
                if hours == 0 and minutes == 0:
                    duration_text = f"{int(seconds)} sec{'s' if seconds > 1 else ''}"
                
                # Format distance text
                if total_distance_meters >= 1000:
                    distance_text = f"{total_distance_meters/1000:.1f} km"
                else:
                    distance_text = f"{total_distance_meters} m"
                
                # Calculate estimated arrival time
                from datetime import datetime, timedelta
                now = datetime.now()
                estimated_arrival = now + timedelta(seconds=total_duration_seconds)
                
                return Response({
                    'duration': {
                        'text': duration_text.strip(),
                        'value': total_duration_seconds
                    },
                    'distance': {
                        'text': distance_text,
                        'value': total_distance_meters
                    },
                    'estimated_arrival_time': estimated_arrival.isoformat()
                })
            
            return Response(
                {'error': 'Could not calculate travel time'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RideRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ride requests
    """
    queryset = RideRequest.objects.all()
    serializer_class = RideRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # If user is staff, return all ride requests
        if self.request.user.is_staff:
            return RideRequest.objects.all()
        
        # For drivers, return only their ride requests
        try:
            driver = Driver.objects.get(user=self.request.user)
            return RideRequest.objects.filter(driver=driver)
        except Driver.DoesNotExist:
            # For passengers, return ride requests related to their rides
            try:
                passenger = Passenger.objects.get(user=self.request.user)
                return RideRequest.objects.filter(ride__passenger=passenger)
            except Passenger.DoesNotExist:
                return RideRequest.objects.none()
    
    @swagger_auto_schema(
        operation_description="Accept or reject a ride request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['ACCEPTED', 'REJECTED']
                )
            }
        ),
        responses={
            200: openapi.Response('Request status updated successfully'),
            400: openapi.Response('Invalid status'),
            403: openapi.Response('Not authorized to update this request'),
            404: openapi.Response('Request not found')
        }
    )
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Allow a driver to accept or reject a ride request"""
        try:
            ride_request = self.get_object()
            
            # Verify the request belongs to the current driver
            try:
                driver = Driver.objects.get(user=request.user)
                if ride_request.driver != driver:
                    return Response(
                        {'error': 'You are not authorized to update this request'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Driver.DoesNotExist:
                return Response(
                    {'error': 'Driver profile not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update the request status - make it case-insensitive
            new_status = request.data.get('status', '').upper()
            if new_status not in ['ACCEPTED', 'REJECTED']:
                return Response(
                    {'error': 'Invalid status. Must be ACCEPTED or REJECTED'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ride_request.status = new_status
            ride_request.save()
            
            # If accepted, update the ride and reject other requests
            if new_status == 'ACCEPTED':
                ride = ride_request.ride
                ride.driver = ride_request.driver
                ride.status = 'ACCEPTED'
                ride.save()
                
                # Reject other pending requests for this ride
                RideRequest.objects.filter(
                    ride=ride, 
                    status='PENDING'
                ).exclude(
                    id=ride_request.id
                ).update(status='REJECTED')
            
            return Response({
                'status': 'Request updated successfully',
                'ride_request': RideRequestSerializer(ride_request).data
            })
            
        except RideRequest.DoesNotExist:
            return Response(
                {'error': 'Ride request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
