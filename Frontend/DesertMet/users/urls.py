from django.urls import path
from .views import *
# from .import views

urlpatterns = [
    path('', home, name="home"),
    path('register/', register),
    path('login/', login, name="login"),
    path('register/', register, name="register" ),
    path('data/', view_data, name="view"),
    path('admin/', admin, name="admin"),
    path('stations/', gestion_station, name="gestion_station"),
    path('ajouter/', ajouter_station, name="ajouter_station"),
    path('surveillance/', surveillance_systeme, name="surveillance"),
    path('gestion_donnes/', gestion_donnees, name="gestion_donnees"),
    
]




