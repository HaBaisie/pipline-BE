from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Profile, Zone, State, Area, Unit, PipelineRoute, PipelineFault

# CustomUserAdmin definition
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Hierarchy', {'fields': ('profile',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile)

# Register other models
admin.site.register(Zone)
admin.site.register(State)
admin.site.register(Area)
admin.site.register(Unit)

# PipelineRouteAdmin
@admin.register(PipelineRoute)
class PipelineRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'get_length')
    search_fields = ('name',)
    list_filter = ('state',)

    def get_length(self, obj):
        return len(obj.coordinates)  # This could represent the number of coordinates or a custom calculation
    get_length.short_description = 'Route Length'

# PipelineFaultAdmin
@admin.register(PipelineFault)
class PipelineFaultAdmin(admin.ModelAdmin):
    list_display = ('pipeline_route', 'get_latitude', 'get_longitude', 'reported_at')
    search_fields = ('description',)
    list_filter = ('pipeline_route', 'reported_at')

    def get_latitude(self, obj):
        return obj.fault_coordinates.get('latitude', 'N/A')
    get_latitude.short_description = 'Latitude'

    def get_longitude(self, obj):
        return obj.fault_coordinates.get('longitude', 'N/A')
    get_longitude.short_description = 'Longitude'
