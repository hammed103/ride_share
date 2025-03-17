from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import views_auth

router = DefaultRouter()
router.register(r'drivers', views.DriverViewSet)
router.register(r'passengers', views.PassengerViewSet)
router.register(r'rides', views.RideViewSet)
router.register(r'match', views.RideMatchingViewSet, basename='match')
router.register(r'navigation', views.NavigationViewSet, basename='navigation')
router.register(r'ride-requests', views.RideRequestViewSet, basename='ride-requests')

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/register/', views_auth.RegisterView.as_view(), name='register'),
    path('auth/driver/register/', views_auth.DriverRegisterView.as_view(), name='driver_register'),
    path('auth/login/', views_auth.LoginView.as_view(), name='login'),
    path('auth/logout/', views_auth.LogoutView.as_view(), name='logout'),
    path('auth/user/', views_auth.UserView.as_view(), name='user'),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
] 