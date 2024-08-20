from django.shortcuts import render
from rest_framework import generics, status, permissions, viewsets
from django.contrib.auth import get_user_model, authenticate, login as django_login
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import logout as django_logout
from .serializers import UserSerializer, LoginSerializer, PipelineRouteAndFaultSerializer
from .models import PipelineRoute, Profile

User = get_user_model()

class IsHigherRole(permissions.BasePermission):
    """
    Custom permission to only allow users with a higher or equal role to create users.
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            profile = Profile.objects.get(user=request.user)
            role = profile.role

            if role == Profile.NATIONAL:
                return True  # National can create users at any level
            elif role == Profile.ZONAL:
                return 'role' in request.data and request.data['role'] in [Profile.STATE]
            elif role == Profile.STATE:
                return 'role' in request.data and request.data['role'] in [Profile.AREA]
            elif role == Profile.AREA:
                return 'role' in request.data and request.data['role'] in [Profile.UNIT]
            return False
        return True

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsHigherRole]  # Ensure user is logged in and has permission

    def perform_create(self, serializer):
        serializer.save()

from rest_framework.permissions import AllowAny

class UserLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                django_login(request, user)

                # Check if the user is authorized based on your criteria
                is_authorized = True  # or whatever logic you want to apply here

                return Response({
                    "message": "Login successful",
                    "isAuthorized": is_authorized
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PipelineRouteAndFaultViewSet(viewsets.ModelViewSet):
    serializer_class = PipelineRouteAndFaultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        queryset = PipelineRoute.objects.all()

        if profile.role == Profile.NATIONAL:
            return queryset
        elif profile.role == Profile.ZONAL:
            return queryset.filter(state__zone=profile.zone)
        elif profile.role == Profile.STATE:
            return queryset.filter(state=profile.state)
        elif profile.role == Profile.AREA:
            return queryset.filter(state__area=profile.area)
        elif profile.role == Profile.UNIT:
            return queryset.filter(state__area__unit=profile.unit)
        
        return queryset.none()  # Fallback to no data if no role matches


class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

