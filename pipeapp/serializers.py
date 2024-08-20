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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            profile = Profile.objects.get(user=request.user)
            if profile.role == Profile.NATIONAL:
                # National can see all fields
                return representation
            elif profile.role == Profile.ZONAL:
                # Zone users see zone, state, area, and unit
                return self._filter_profile_fields(representation, include=['zone', 'state', 'area', 'unit'])
            elif profile.role == Profile.STATE:
                # State users see state, area, and unit
                return self._filter_profile_fields(representation, include=['state', 'area', 'unit'])
            elif profile.role == Profile.AREA:
                # Area users see area and unit
                return self._filter_profile_fields(representation, include=['area', 'unit'])
            elif profile.role == Profile.UNIT:
                # Unit users see only the unit
                return self._filter_profile_fields(representation, include=['unit'])
        return representation

    def _filter_profile_fields(self, representation, include=None):
        """
        Helper method to filter fields based on the included list.
        """
        if include is None:
            include = []

        profile_data = representation.get('profile', {})
        # Create a new dictionary with only the fields in `include`
        filtered_profile_data = {key: profile_data.get(key) for key in include}
        representation['profile'] = filtered_profile_data

        return representation


from rest_framework import serializers
from .models import Profile, CustomUser

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role', 'location', 'zone', 'state', 'area', 'unit']

class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile']



from rest_framework import serializers
from .models import PipelineRoute, PipelineFault, State

# Serializer for individual faults
class PipelineFaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineFault
        fields = ['fault_coordinates', 'description', 'reported_at', 'status']

class PipelineRouteAndFaultSerializer(serializers.ModelSerializer):
    state = serializers.CharField()  # Accept state as a char field (name)
    id = serializers.ReadOnlyField()
    name = serializers.CharField()
    coordinates = serializers.JSONField()
    status = serializers.SerializerMethodField()
    faults = PipelineFaultSerializer(many=True)

    class Meta:
        model = PipelineRoute
        fields = ['id', 'name', 'state', 'coordinates', 'status', 'faults']
        read_only_fields = ['id']

    def get_status(self, obj):
        if obj.faults.filter(status='critical').exists():
            return 'critical'
        elif obj.faults.filter(status='warning').exists():
            return 'warning'
        return 'normal'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            profile = Profile.objects.get(user=request.user)
            if profile.role == Profile.NATIONAL:
                # National sees all fields
                return representation
            elif profile.role == Profile.ZONAL:
                # Zone users see only zone-related data
                if instance.state.zone != profile.zone:
                    return {}
            elif profile.role == Profile.STATE:
                # State users see only state-related data
                if instance.state != profile.state:
                    return {}
            elif profile.role == Profile.AREA:
                # Area users see only area-related data
                if instance.state.area != profile.area:
                    return {}
            elif profile.role == Profile.UNIT:
                # Unit users see only unit-related data
                if instance.state.area.unit != profile.unit:
                    return {}
        return representation

