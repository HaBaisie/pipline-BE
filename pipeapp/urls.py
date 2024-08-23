from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token  # Import the obtain_auth_token view
from .views import (
    UserRegisterView, 
    UserLoginView, 
    PipelineRouteAndFaultViewSet,
    UserLogoutView
)

# Create a router and register the viewset
router = DefaultRouter()
router.register(r'pipeline-routes-viewset', PipelineRouteAndFaultViewSet, basename='pipeline-route-viewset')

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'), 
    path('', include(router.urls)),  # Include the router's URLs
]
