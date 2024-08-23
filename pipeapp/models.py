from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


CustomUser = get_user_model()

class Profile(models.Model):
    NATIONAL = 'National'
    ZONAL = 'Zonal'
    STATE = 'State'
    AREA = 'Area'
    UNIT = 'Unit'

    ROLE_CHOICES = [
        (NATIONAL, 'National'),
        (ZONAL, 'Zonal'),
        (STATE, 'State'),
        (AREA, 'Area'),
        (UNIT, 'Unit'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=UNIT)
    location = models.CharField(max_length=255, blank=True, null=True)
    zone = models.ForeignKey('Zone', on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey('Unit', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class CustomUser(AbstractUser):
    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
class PipelineRoute(models.Model):
    name = models.CharField(max_length=255, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    coordinates = models.JSONField()  # Stores the longitude and latitude as a list of dictionaries

    def __str__(self):
        return self.name

class PipelineFault(models.Model):
    FAULT_STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical')
    ]
    
    pipeline_route = models.ForeignKey(PipelineRoute, on_delete=models.CASCADE, related_name='faults')
    fault_coordinates = models.JSONField()  # Stores the longitude and latitude of the fault
    description = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=FAULT_STATUS_CHOICES, default='normal')

    def __str__(self):
        return f"Fault in {self.pipeline_route.name} at {self.fault_coordinates}"
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
