"""
users/admin.py
Configuration de l'interface d'administration Django
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Station, WeatherData, AdminLog


# Personnalisation de l'affichage des utilisateurs
class UserAdmin(BaseUserAdmin):
    """Interface d'administration pour le modèle User"""

    list_display = ('email', 'fullname', 'is_desert_admin', 'is_staff', 'date_joined')
    list_filter = ('is_desert_admin', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'fullname')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('fullname',)}),
        ('Permissions', {
            'fields': ('is_desert_admin', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'fullname', 'password1', 'password2', 'is_desert_admin'),
        }),
    )


class StationAdmin(admin.ModelAdmin):
    """Interface d'administration pour le modèle Station"""

    list_display = ('nom', 'get_localisation', 'energie', 'communication', 'status', 'date_creation')
    list_filter = ('status', 'energie', 'communication')
    search_fields = ('nom',)
    list_editable = ('status',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'latitude', 'longitude')
        }),
        ('Configuration technique', {
            'fields': ('energie', 'communication', 'status')
        }),
        ('Capteurs disponibles', {
            'fields': (
                'capteur_temperature',
                'capteur_pression',
                'capteur_vent',
                'capteur_ensoleillement',
                'capteur_precipitation'
            )
        }),
    )


class WeatherDataAdmin(admin.ModelAdmin):
    """Interface d'administration pour le modèle WeatherData"""

    list_display = ('station', 'timestamp', 'temperature', 'pression', 'vitesse_vent', 'precipitation', 'ensoleillement')
    list_filter = ('station', 'timestamp')
    search_fields = ('station__nom',)
    date_hierarchy = 'timestamp'


class AdminLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour le modèle AdminLog"""

    list_display = ('admin', 'action_type', 'timestamp', 'station_concerne')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('admin__email', 'description', 'station_concerne__nom')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


# Enregistrement des modèles dans l'admin
admin.site.register(User, UserAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(WeatherData, WeatherDataAdmin)
admin.site.register(AdminLog, AdminLogAdmin)