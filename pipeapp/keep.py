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