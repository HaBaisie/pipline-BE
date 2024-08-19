from django.core.management.base import BaseCommand
from pipeapp.models import Zone, State

class Command(BaseCommand):
    help = 'Populate the database with geopolitical zones and states'

    def handle(self, *args, **kwargs):
        # Define zones and states
        zones = {
            'North Central': ['Benue', 'Kogi', 'Kwara', 'Nasarawa', 'Niger', 'Plateau', 'Abuja'],
            'North East': ['Adamawa', 'Bauchi', 'Borno', 'Gombe', 'Taraba', 'Yobe'],
            'North West': ['Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Sokoto', 'Zamfara'],
            'South East': ['Abia', 'Anambra', 'Ebonyi', 'Enugu', 'Imo'],
            'South South': ['Akwa Ibom', 'Bayelsa', 'Cross River', 'Delta', 'Edo', 'Rivers'],
            'South West': ['Ekiti', 'Lagos', 'Ogun', 'Ondo', 'Osun', 'Oyo']
        }

        for zone_name, states in zones.items():
            # Create or get zone
            zone, created = Zone.objects.get_or_create(name=zone_name)
            for state_name in states:
                # Create or get state
                State.objects.get_or_create(name=state_name, defaults={'zone': zone})

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with zones and states'))
