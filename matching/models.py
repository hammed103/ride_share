from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    location = models.JSONField(null=True, blank=True)  # Store (latitude, longitude)
    rating = models.FloatField(default=5.0)
    preferences = models.JSONField(default=dict)  # { "smoking": False, "music": True, "pets": False }
    available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"

class Passenger(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    pickup_location = models.JSONField(null=True, blank=True)  # (latitude, longitude)
    destination = models.JSONField(null=True, blank=True)  # (latitude, longitude)
    preferences = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"

class Ride(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    pickup_location = models.JSONField()
    destination = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='PENDING'
    )
    
class RideRequest(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='requests')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('REJECTED', 'Rejected'),
            ('EXPIRED', 'Expired')
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('ride', 'driver')
    
    def __str__(self):
        return f"Request for ride {self.ride.id} to driver {self.driver}"
    