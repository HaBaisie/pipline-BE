from django.shortcuts import render
from rest_framework import generics, status, permissions, viewsets
from django.contrib.auth import get_user_model, authenticate, login as django_login, logout as django_logout
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from .models import CustomUser, PipelineRoute, Profile, PipelineFault
from .serializers import UserSerializer, LoginSerializer, PipelineRouteAndFaultSerializer,UserDetailSerializer,  PipelineRouteSerializer, PipelineFaultSerializer


User = get_user_model()

# User registration view
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User login view
class UserLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Log the user in
            django_login(request, user)

            # Generate or retrieve a token for the user
            token, created = Token.objects.get_or_create(user=user)

            # Serialize the user data including profile
            user_data = UserDetailSerializer(user).data

            return Response({
                "message": "Login successful",
                "token": token.key,  # Return the token
                "user": user_data  # Return the user data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PipelineRoute views
class PipelineRouteListCreateView(generics.ListCreateAPIView):
    queryset = PipelineRoute.objects.all()
    serializer_class = PipelineRouteSerializer

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PipelineRouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PipelineRoute.objects.all()
    serializer_class = PipelineRouteSerializer

# PipelineFault views
class PipelineFaultListCreateView(generics.ListCreateAPIView):
    queryset = PipelineFault.objects.all()
    serializer_class = PipelineFaultSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PipelineFaultDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PipelineFault.objects.all()
    serializer_class = PipelineFaultSerializer

class PipelineRouteAndFaultViewSet(viewsets.ModelViewSet):
    serializer_class = PipelineRouteAndFaultSerializer
    authentication_classes = [TokenAuthentication, BasicAuthentication]  # Use TokenAuthentication for token-based auth
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
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
