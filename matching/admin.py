from django.contrib import admin
from .models import Driver, Passenger, Ride

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'rating', 'available')
    list_filter = ('available', 'rating')
    search_fields = ('firstname', 'lastname')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname')
    search_fields = ('firstname', 'lastname')

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'passenger', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('driver__firstname', 'driver__lastname', 
                    'passenger__firstname', 'passenger__lastname')
    readonly_fields = ('created_at',)
