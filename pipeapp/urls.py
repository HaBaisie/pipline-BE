from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, 
    UserLoginView, 
    PipelineRouteAndFaultViewSet
)

# Create a router and register the viewset
router = DefaultRouter()
router.register(r'pipeline-routes-viewset', PipelineRouteAndFaultViewSet, basename='pipeline-route-viewset')

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    # path('pipeline-routes/', PipelineRouteListCreateView.as_view(), name='pipeline-routes-list-create'),
    # path('pipeline-routes/<int:pk>/', PipelineRouteDetailView.as_view(), name='pipeline-routes-detail'),
    # path('pipeline-faults/', PipelineFaultListCreateView.as_view(), name='pipeline-faults-list-create'),
    # path('pipeline-faults/<int:pk>/', PipelineFaultDetailView.as_view(), name='pipeline-faults-detail'),
    path('', include(router.urls)),  # Include the router's URLs
]
