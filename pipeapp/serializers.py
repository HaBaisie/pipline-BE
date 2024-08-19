from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Zone, State, Area, Unit, PipelineRoute, PipelineFault

CustomUser = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    zone = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    area = serializers.CharField(required=False)
    unit = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ['id', 'role', 'location', 'zone', 'state', 'area', 'unit']
        read_only_fields = ['id']

    def create_or_get_instance(self, model_class, name, related_field=None):
        if related_field:
            instance, created = model_class.objects.get_or_create(name=name, **related_field)
        else:
            instance, created = model_class.objects.get_or_create(name=name)
        return instance

    def create(self, validated_data):
        zone_name = validated_data.pop('zone', None)
        state_name = validated_data.pop('state', None)
        area_name = validated_data.pop('area', None)
        unit_name = validated_data.pop('unit', None)

        profile = Profile.objects.create(**validated_data)

        if zone_name:
            profile.zone = self.create_or_get_instance(Zone, zone_name)
        if state_name:
            profile.state = self.create_or_get_instance(State, state_name, {'zone': profile.zone})
        if area_name:
            profile.area = self.create_or_get_instance(Area, area_name, {'state': profile.state})
        if unit_name:
            profile.unit = self.create_or_get_instance(Unit, unit_name, {'area': profile.area})

        profile.save()
        return profile

    def update(self, instance, validated_data):
        zone_name = validated_data.pop('zone', None)
        state_name = validated_data.pop('state', None)
        area_name = validated_data.pop('area', None)
        unit_name = validated_data.pop('unit', None)

        if zone_name:
            instance.zone = self.create_or_get_instance(Zone, zone_name)
        if state_name:
            instance.state = self.create_or_get_instance(State, state_name, {'zone': instance.zone})
        if area_name:
            instance.area = self.create_or_get_instance(Area, area_name, {'state': instance.state})
        if unit_name:
            instance.unit = self.create_or_get_instance(Unit, unit_name, {'area': instance.area})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    profile = ProfileSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'profile']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create Profile instance
        ProfileSerializer().create({
            **profile_data,
            'user': user,
        })

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


from rest_framework import serializers
from .models import PipelineRoute, State, PipelineFault

class PipelineRouteSerializer(serializers.ModelSerializer):
    state = serializers.CharField()  # Accept state as a char field (name)

    class Meta:
        model = PipelineRoute
        fields = ['id', 'name', 'state', 'coordinates']
        read_only_fields = ['id']

    def create(self, validated_data):
        state_name = validated_data.pop('state')
        try:
            state = State.objects.get(name=state_name)
        except State.DoesNotExist:
            raise serializers.ValidationError({'state': f"State '{state_name}' does not exist."})

        pipeline_route = PipelineRoute.objects.create(state=state, **validated_data)
        return pipeline_route

    def update(self, instance, validated_data):
        state_name = validated_data.pop('state', None)
        if state_name:
            try:
                state = State.objects.get(name=state_name)
            except State.DoesNotExist:
                raise serializers.ValidationError({'state': f"State '{state_name}' does not exist."})
            instance.state = state

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
from rest_framework import serializers
from .models import PipelineRoute, PipelineFault, State

# Serializer for individual faults
class PipelineFaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineFault
        fields = ['fault_coordinates', 'description', 'reported_at', 'status']

# Serializer for PipelineRoute, including faults and computed status
class PipelineRouteAndFaultSerializer(serializers.ModelSerializer):
    state = serializers.CharField()  # Accept state as a char field (name)
    id = serializers.ReadOnlyField()
    name = serializers.CharField()  # Allow name to be provided and updated
    coordinates = serializers.JSONField()  # Include coordinates as a JSON field
    status = serializers.SerializerMethodField()  # Use a method field to get the overall status
    faults = PipelineFaultSerializer(many=True)  # Allow creating faults with the route

    class Meta:
        model = PipelineRoute
        fields = [
            'id', 'name', 'state', 'coordinates', 
            'status', 'faults'
        ]
        read_only_fields = ['id']

    def get_status(self, obj):
        # Determine the overall status based on related faults
        if obj.faults.filter(status='critical').exists():
            return 'critical'
        elif obj.faults.filter(status='warning').exists():
            return 'warning'
        return 'normal'

    def create(self, validated_data):
        # Extract faults data from validated data
        faults_data = validated_data.pop('faults', [])
        
        # Handle state
        state_name = validated_data.pop('state')
        state, _ = State.objects.get_or_create(name=state_name)

        # Check if the pipeline route with the same name already exists
        pipeline_route, created = PipelineRoute.objects.update_or_create(
            name=validated_data.get('name'),
            defaults={
                'state': state,
                'coordinates': validated_data.get('coordinates')
            }
        )

        # If updating, clear existing faults
        if not created:
            pipeline_route.faults.all().delete()

        # Create new faults
        for fault_data in faults_data:
            PipelineFault.objects.create(pipeline_route=pipeline_route, **fault_data)

        return pipeline_route

    def update(self, instance, validated_data):
        # Handle state
        state_name = validated_data.pop('state', None)
        if state_name:
            try:
                state = State.objects.get(name=state_name)
            except State.DoesNotExist:
                raise serializers.ValidationError({'state': f"State '{state_name}' does not exist."})
            instance.state = state
        
        # Update pipeline route attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update or create related faults
        faults_data = validated_data.pop('faults', None)
        if faults_data is not None:
            # First, clear existing faults
            instance.faults.all().delete()
            
            # Then, create new faults
            for fault_data in faults_data:
                PipelineFault.objects.create(pipeline_route=instance, **fault_data)

        return instance
