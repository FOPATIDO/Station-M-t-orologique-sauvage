"""
users/urls.py
Routes URL pour l'application DesertMet
"""

from django.urls import path
from .views import *

urlpatterns = [
    # Pages publiques
    path('', home, name='home'),
    path('login/', login_view, name="login"),
    path('register/', register, name="register"),
    path('logout/', logout_view, name="logout"),

    # Dashboard utilisateur
    path('dashboard/', view_data, name="view"),
    path('data/', view_data, name="view_alt"),

    # Dashboard admin
    path('admin-dashboard/', admin_dashboard, name="admin_dashboard"),

    # Gestion des stations
    path('stations/', gestion_station, name="gestion_station"),
    path('stations/ajouter/', ajouter_station, name="ajouter_station"),

    # Surveillance et données
    path('surveillance/', surveillance_systeme, name="surveillance"),
    path('gestion-donnees/', gestion_donnees, name="gestion_donnees"),

    # API endpoints
    path('api/stations/status/', api_stations_status, name="api_stations_status"),
    path('api/data/recent/', api_recent_data, name="api_recent_data"),
    path('api/data/recent/<uuid:station_id>/', api_recent_data, name="api_recent_data_station"),
    # URLs pour la gestion des stations
    path('stations/', gestion_station, name="gestion_station"),
    path('stations/ajouter/', ajouter_station, name="ajouter_station"),
    path('stations/modifier/<uuid:station_id>/', modifier_station, name="modifier_station"),
    path('stations/supprimer/<uuid:station_id>/', supprimer_station, name="supprimer_station"),

    # URL pour l'export des données
    path('export-donnees/', export_donnees, name="export_donnees"),
]