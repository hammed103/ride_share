from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Driver, Passenger, Ride, RideRequest
from .services.distance_calculator import calculate_distance

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'firstname', 'lastname', 'location', 'rating', 'preferences', 'available']

class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = ['id', 'firstname', 'lastname', 'pickup_location', 'destination', 'preferences']

class RideMatchRequestSerializer(serializers.Serializer):
    passenger_id = serializers.IntegerField()
    pickup_location = serializers.JSONField()
    destination = serializers.JSONField()
    preferences = serializers.JSONField(required=False)

class RouteRequestSerializer(serializers.Serializer):
    origin = serializers.JSONField()
    destination = serializers.JSONField()
    waypoints = serializers.JSONField(required=False)

class RideSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    passenger_name = serializers.SerializerMethodField()
    trip_distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = ['id', 'driver', 'driver_name', 'passenger', 'passenger_name', 
                 'pickup_location', 'destination', 'trip_distance', 'created_at', 'status']
    
    def get_driver_name(self, obj):
        return f"{obj.driver.firstname} {obj.driver.lastname}" if obj.driver else None
    
    def get_passenger_name(self, obj):
        return f"{obj.passenger.firstname} {obj.passenger.lastname}" if obj.passenger else None
    
    def get_trip_distance(self, obj):
        try:
            if obj.pickup_location and obj.destination:
                distance = calculate_distance(obj.pickup_location, obj.destination)
                return {
                    "value": round(distance, 2),
                    "unit": "km"
                }
        except Exception as e:
            import logging
            logger = logging.getLogger('matching')
            logger.error(f"Error calculating trip distance for ride {obj.id}: {str(e)}")
        return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    firstname = serializers.CharField(required=True, write_only=True)
    lastname = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'firstname', 'lastname']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove the password2 field as it's not needed for User creation
        validated_data.pop('password2', None)
        
        # Extract firstname and lastname before creating the User
        firstname = validated_data.pop('firstname')
        lastname = validated_data.pop('lastname')
        
        # Create the User with the correct field names
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=firstname,  # Note the underscore here
            last_name=lastname     # Note the underscore here
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        # Create associated passenger profile
        Passenger.objects.create(
            user=user,
            firstname=firstname,
            lastname=lastname,
            preferences={}
        )
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class DriverRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    firstname = serializers.CharField(required=True, write_only=True)
    lastname = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'firstname', 'lastname']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Remove the password2 field as it's not needed for User creation
        validated_data.pop('password2', None)
        
        # Extract firstname and lastname before creating the User
        firstname = validated_data.pop('firstname')
        lastname = validated_data.pop('lastname')
        
        # Create the User with the correct field names
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=firstname,
            last_name=lastname
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        # Create associated driver profile
        Driver.objects.create(
            user=user,
            firstname=firstname,
            lastname=lastname,
            location=None,  # Will be updated when driver starts the app
            rating=5.0,     # Default rating for new drivers
            preferences={},
            available=True
        )
        
        return user 

class RideRequestSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    passenger_name = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    distance_to_pickup = serializers.SerializerMethodField()
    trip_distance = serializers.SerializerMethodField()
    
    class Meta:
        model = RideRequest
        fields = ['id', 'ride', 'driver', 'driver_name', 'passenger_name',
                 'pickup_location', 'destination', 'distance_to_pickup', 
                 'trip_distance', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        return f"{obj.driver.firstname} {obj.driver.lastname}" if obj.driver else None
    
    def get_passenger_name(self, obj):
        return f"{obj.ride.passenger.firstname} {obj.ride.passenger.lastname}" if obj.ride.passenger else None
    
    def get_pickup_location(self, obj):
        return obj.ride.pickup_location
    
    def get_destination(self, obj):
        return obj.ride.destination
        
    def get_distance_to_pickup(self, obj):
        try:
            if obj.driver and obj.driver.location and obj.ride.pickup_location:
                distance = calculate_distance(obj.driver.location, obj.ride.pickup_location)
                return {
                    "value": round(distance, 2),
                    "unit": "km"
                }
        except Exception as e:
            import logging
            logger = logging.getLogger('matching')
            logger.error(f"Error calculating distance for ride request {obj.id}: {str(e)}")
        return None
        
    def get_trip_distance(self, obj):
        try:
            if obj.ride.pickup_location and obj.ride.destination:
                distance = calculate_distance(obj.ride.pickup_location, obj.ride.destination)
                return {
                    "value": round(distance, 2),
                    "unit": "km"
                }
        except Exception as e:
            import logging
            logger = logging.getLogger('matching')
            logger.error(f"Error calculating trip distance for ride request {obj.id}: {str(e)}")
        return None 