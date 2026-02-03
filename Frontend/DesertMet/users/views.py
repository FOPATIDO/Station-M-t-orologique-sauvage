from django.shortcuts import render

# Create your views here.




def home (request):
  return render(request, "accueil.html");

def login(request):
  return render(request, "login.html");

def register(request):
  return render(request, "register.html");

def view_data(request):
  return render(request, "dashboard_users.html");

def admin(request):
  return render(request, "admin_dashboard.html");

def gestion_station(request):
  return render(request, "gestion_station.html");

def ajouter_station(request):
  return render(request, "ajout_station.html");

def surveillance_systeme(request):
  return render(request, "surveillance_syteme.html");

def gestion_donnees(request):
  return render(request, "gestion_donnees.html");