"""
users/views.py
Gestion de la logique métier et des vues pour l'application DesertMet
"""
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Avg, Max, Min,Q
from django.utils import timezone
import csv
import json
import threading
import time
import random
from django.utils import timezone
from .models import Station, WeatherData

from .models import User, Station, WeatherData, AdminLog
from .forms import LoginForm, RegisterForm, StationForm

# ==============================================
# VUES D'AUTHENTIFICATION
# ==============================================

def home(request):
    """
    Page d'accueil du site
    """
    # Si l'utilisateur est déjà connecté, rediriger selon son type
    if request.user.is_authenticated:
        if request.user.email.endswith('@desertmet.com'):
            return redirect('admin_dashboard')
        else:
            return redirect('view')

    return render(request, "accueil.html", {
        'title': 'DesertMet - Accueil'
    })


@csrf_protect
def login_view(request):
    """
    Gestion de la connexion utilisateur
    """

    # Si déjà connecté
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # NORMALISATION: convertir en minuscules
        email = email.lower()
        print(f"Email normalisé: {email}")

        if not email or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
        else:
            try:
                # Chercher l'utilisateur avec email normalisé
                user = User.objects.get(email=email)
                print(f"Utilisateur trouvé: {user.email}")

                # Vérifier le mot de passe
                if user.check_password(password):
                    print("Mot de passe correct")

                    # Connexion Django
                    auth_login(request, user)

                    # Session de 2 jours
                    request.session.set_expiry(172800)

                    # Redirection selon le type d'utilisateur
                    if email.endswith('@desertmet.com'):
                        if user.is_desert_admin:
                            return redirect('admin_dashboard')
                        else:
                            messages.error(request, "Accès administrateur refusé.")
                    else:
                        return redirect('view')

                else:
                    print("Mot de passe incorrect")
                    messages.error(request, "Email ou mot de passe incorrect.")

            except User.DoesNotExist:
                print(f"Utilisateur '{email}' non trouvé dans la BD")
                # Liste tous les utilisateurs pour debug
                all_users = User.objects.all()
                print("Tous les utilisateurs dans la BD:")
                for u in all_users:
                    print(f"  - {u.email} (admin: {u.is_desert_admin})")
                messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, "login.html", {
        'title': 'Connexion',
        'email_value': request.POST.get('email', '') if request.method == 'POST' else ''
    })

@csrf_protect
def register(request):
    """
    Gestion de l'inscription utilisateur
    RÈGLE : Bloquer les inscriptions avec @desertmet.com
    """

    # Si l'utilisateur est déjà connecté, rediriger
    if request.user.is_authenticated:
        if request.user.email.endswith('@desertmet.com'):
            return redirect('admin')
        else:
            return redirect('view')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            # RÈGLE CRITIQUE : Vérifier que ce n'est pas une adresse admin
            if email.endswith('@desertmet.com'):
                messages.error(request, "Adresse privée. Les adresses @desertmet.com sont réservées aux administrateurs.")
                return render(request, "register.html", {
                    'form': form,
                    'title': 'Inscription'
                })

            # Créer l'utilisateur
            try:
                user = User.objects.create_user(
                    email=email,
                    fullname=form.cleaned_data['fullname'],
                    password=form.cleaned_data['password1']
                )

                messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
                return redirect('login')

            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {
        'form': form,
        'title': 'Inscription'
    })


def logout_view(request):
    """
    Déconnexion de l'utilisateur
    """
    auth_logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


# ==============================================
# DÉCORATEURS PERSONNALISÉS
# ==============================================

def session_required(view_func):
    """
    Décorateur pour vérifier qu'une session active existe
    Redirige vers la page de login si pas de session
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur est un admin DesertMet
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('login')

        # Vérifier que c'est bien un admin DesertMet
        if not (request.user.email.endswith('@desertmet.com') and request.user.is_desert_admin):
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('view')

        return view_func(request, *args, **kwargs)
    return wrapper


# ==============================================
# VUES UTILISATEURS STANDARD
# ==============================================

@session_required
def view_data(request):
    """
    Dashboard utilisateur standard
    Affiche les 20 derniers relevés de WeatherData
    RÈGLE : Accessible uniquement avec session active
    """

    # Vérifier que ce n'est pas un admin qui tente d'accéder
    if request.user.email.endswith('@desertmet.com') and request.user.is_desert_admin:
        messages.warning(request, "Les administrateurs doivent utiliser le dashboard admin.")
        return redirect('admin_dashboard')

    # Récupérer les 20 derniers relevés météo
    derniers_releves = WeatherData.objects.select_related('station').order_by('-timestamp')[:20]

    # Statistiques rapides
    total_stations = Station.objects.count()
    stations_actives = Station.objects.filter(status='ACTIF').count()

    # Si l'utilisateur a des stations favorites (à implémenter plus tard)
    stations_favorites = Station.objects.all()[:5]  # Pour l'instant, toutes

    return render(request, "dashboard_users.html", {
        'title': 'Dashboard Utilisateur',
        'user': request.user,
        'derniers_releves': derniers_releves,
        'total_stations': total_stations,
        'stations_actives': stations_actives,
        'stations_favorites': stations_favorites,
        'now': timezone.now()
    })


# ==============================================
# VUES ADMINISTRATEUR
# ==============================================

@admin_required
def admin_dashboard(request):
    """
    Dashboard administrateur
    Accessible uniquement aux emails @desertmet.com
    """

    # Statistiques pour le dashboard admin
    total_stations = Station.objects.count()
    stations_actives = Station.objects.filter(status='ACTIF').count()
    stations_maintenance = Station.objects.filter(status='MAINTENANCE').count()
    stations_panne = Station.objects.filter(status='EN_PANNE').count()

    # Derniers relevés (toutes stations)
    derniers_releves = WeatherData.objects.select_related('station').order_by('-timestamp')[:10]

    # Dernières actions admin
    derniers_logs = AdminLog.objects.select_related('admin', 'station_concerne').order_by('-timestamp')[:10]

    # Répartition par type d'énergie
    from users import models
    energie_stats = Station.objects.values('energie').annotate(
        count=Count('id'),
        actives=Count('id', filter= Q(status='ACTIF'))
    )

    # Données pour les graphiques
    stations_par_status = {
        'ACTIF': stations_actives,
        'MAINTENANCE': stations_maintenance,
        'EN_PANNE': stations_panne
    }

    return render(request, "admin_dashboard.html", {
        'title': 'Dashboard Administrateur',
        'user': request.user,
        'total_stations': total_stations,
        'stations_actives': stations_actives,
        'stations_maintenance': stations_maintenance,
        'stations_panne': stations_panne,
        'stations_par_status': json.dumps(stations_par_status),
        'derniers_releves': derniers_releves,
        'derniers_logs': derniers_logs,
        'energie_stats': energie_stats,
        'now': timezone.now()
    })


@admin_required
def gestion_station(request):
    """
    Gestion des stations (liste)
    """
    stations = Station.objects.all().order_by('nom')

    # Calcul des statistiques
    stats = {
        'total': stations.count(),
        'actives': stations.filter(status='ACTIF').count(),
        'maintenance': stations.filter(status='MAINTENANCE').count(),
        'panne': stations.filter(status='EN_PANNE').count(),
    }

    return render(request, "gestion_station.html", {
        'title': 'Gestion des Stations',
        'stations': stations,
        'stats': stats,
        'user': request.user
    })


@admin_required
def ajouter_station(request):
    """
    Formulaire d'ajout d'une nouvelle station
    """
    if request.method == 'POST':
        form = StationForm(request.POST)
        if form.is_valid():
            station = form.save()

            # Log de l'action
            AdminLog.creer_log(
                admin=request.user,
                action_type=AdminLog.ActionType.CREATE_STATION,
                description=f"Création de la station {station.nom}",
                station=station,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Station {station.nom} créée avec succès !")
            return redirect('gestion_station')
    else:
        form = StationForm()

    return render(request, "ajout_station.html", {
        'title': 'Ajouter une Station',
        'form': form,
        'user': request.user
    })


@admin_required
def surveillance_systeme(request):
    """
    Surveillance système avec ratios et batterie
    """
    # Récupérer toutes les stations
    stations = Station.objects.all().order_by('status', 'nom')

    # Calcul des ratios
    total = stations.count()
    actives = stations.filter(status='ACTIF').count()
    ratio_actives = (actives / total * 100) if total > 0 else 0

    # Dernières données de chaque station
    stations_data = []
    for station in stations:
        derniere_donnee = WeatherData.objects.filter(station=station).order_by('-timestamp').first()

        # Simulation du niveau de batterie
        import random
        niveau_batterie = random.randint(20, 100)

        stations_data.append({
            'station': station,
            'derniere_donnee': derniere_donnee,
            'niveau_batterie': niveau_batterie,
            'derniere_communication': derniere_donnee.timestamp if derniere_donnee else None
        })

    # Statistiques globales
    stats = {
        'total': total,
        'actives': actives,
        'maintenance': stations.filter(status='MAINTENANCE').count(),
        'panne': stations.filter(status='EN_PANNE').count(),
        'ratio_actives': round(ratio_actives, 2),
        'solaire': stations.filter(energie='SOLAIRE').count(),
        'batterie': stations.filter(energie='BATTERIE').count(),
        'hybride': stations.filter(energie='HYBRIDE').count(),
    }

    return render(request, "surveillance_syteme.html", {
        'title': 'Surveillance Système',
        'stations_data': stations_data,
        'stats': stats,
        'user': request.user,
        'now': timezone.now()
    })

@session_required
def gestion_donnees(request):
    """
    Gestion et visualisation des données météorologiques
    Filtrable par date et par station
    """

    # Récupérer tous les filtres possibles
    stations = Station.objects.all().order_by('nom')

    # Initialiser les filtres
    station_filter = request.GET.get('station', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    # Construire la requête filtrée
    donnees = WeatherData.objects.select_related('station').all()

    if station_filter:
        donnees = donnees.filter(station_id=station_filter)

    if date_debut:
        donnees = donnees.filter(timestamp__gte=date_debut)

    if date_fin:
        donnees = donnees.filter(timestamp__lte=date_fin)

    # Trier par date décroissante
    donnees = donnees.order_by('-timestamp')[:100]  # Limiter à 100 résultats

    # Statistiques sur les données filtrées
    if donnees.exists():
        stats = {
            'moyenne_temp': donnees.aggregate(Avg('temperature'))['temperature__avg'],
            'max_temp': donnees.aggregate(Max('temperature'))['temperature__max'],
            'min_temp': donnees.aggregate(Min('temperature'))['temperature__min'],
            'total_releves': donnees.count()
        }
    else:
        stats = None

    return render(request, "gestion_donnees.html", {
        'title': 'Gestion des Données',
        'donnees': donnees,
        'stations': stations,
        'stats': stats,
        'filtres': {
            'station': station_filter,
            'date_debut': date_debut,
            'date_fin': date_fin
        },
        'user': request.user
    })


# ==============================================
# VUES API/JSON
# ==============================================

@login_required
def api_stations_status(request):
    """
    API pour récupérer le statut des stations (JSON)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=401)

    stations = Station.objects.all().values(
        'id', 'nom', 'status', 'latitude', 'longitude', 'energie'
    )

    return JsonResponse(list(stations), safe=False)


@login_required
def api_recent_data(request, station_id=None):
    """
    API pour récupérer les données récentes (JSON)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=401)

    if station_id:
        donnees = WeatherData.objects.filter(station_id=station_id)
    else:
        donnees = WeatherData.objects.all()

    donnees = donnees.order_by('-timestamp')[:50].values(
        'id', 'station__nom', 'temperature', 'pression',
        'vitesse_vent', 'precipitation', 'ensoleillement', 'timestamp'
    )

    return JsonResponse(list(donnees), safe=False)


@admin_required
def export_donnees(request):
    """
       Export des données météorologiques en format texte (CSV)
       """
    # Récupérer les mêmes filtres que dans gestion_donnees
    station_filter = request.POST.get('station', '')
    date_debut = request.POST.get('date_debut', '')
    date_fin = request.POST.get('date_fin', '')

    # Construire la requête filtrée
    donnees = WeatherData.objects.select_related('station').all()

    if station_filter:
        donnees = donnees.filter(station_id=station_filter)

    if date_debut:
        donnees = donnees.filter(timestamp__gte=date_debut)

    if date_fin:
        donnees = donnees.filter(timestamp__lte=date_fin)

    # Trier par date décroissante
    donnees = donnees.order_by('-timestamp')

    # Créer le nom du fichier
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f'donnees_meteo_export_{timestamp}.txt'

    # Créer le contenu du fichier texte
    content = "=" * 70 + "\n"
    content += "EXPORT DES DONNÉES MÉTÉOROLOGIQUES - DesertMet\n"
    content += "=" * 70 + "\n\n"

    # Informations sur l'export
    content += f"Date d'export : {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    content += f"Nombre de relevés : {donnees.count()}\n"

    if station_filter:
        try:
            station = Station.objects.get(id=station_filter)
            content += f"Station : {station.nom}\n"
        except Station.DoesNotExist:
            content += f"Station : ID {station_filter}\n"
    else:
        content += "Station : Toutes les stations\n"

    if date_debut:
        content += f"Période : à partir du {date_debut}"
        if date_fin:
            content += f" jusqu'au {date_fin}\n"
        else:
            content += "\n"
    content += "\n" + "=" * 70 + "\n\n"

    # En-tête du tableau
    content += f"{'Date/Heure':<20} {'Station':<20} {'Temp (°C)':<12} "
    content += f"{'Pression (hPa)':<15} {'Vent (km/h)':<12} "
    content += f"{'Précip (mm)':<12} {'Soleil (W/m²)':<12} {'Statut':<10}\n"
    content += "-" * 120 + "\n"

    # Données
    for releve in donnees:
        date_str = releve.timestamp.strftime('%d/%m/%Y %H:%M')
        station_nom = releve.station.nom[:18]  # Tronquer si trop long

        # Formater les valeurs (remplacer None par "-")
        temp = f"{releve.temperature:.1f}" if releve.temperature else "-"
        pression = f"{releve.pression:.1f}" if releve.pression else "-"
        vent = f"{releve.vitesse_vent:.1f}" if releve.vitesse_vent else "-"
        precip = f"{releve.precipitation:.1f}" if releve.precipitation else "-"
        soleil = f"{releve.ensoleillement:.1f}" if releve.ensoleillement else "-"

        # Statut de la station
        statut = releve.station.get_status_display()

        content += f"{date_str:<20} {station_nom:<20} {temp:<12} "
        content += f"{pression:<15} {vent:<12} {precip:<12} "
        content += f"{soleil:<12} {statut:<10}\n"

    # Pied de page
    content += "\n" + "=" * 70 + "\n"
    content += "FIN DE L'EXPORT\n"
    content += "Système d'Information Météorologique DesertMet\n"
    content += "© 2026 GIT-3 – Système Météorologique National\n"

    # Créer la réponse HTTP avec le fichier texte
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Log de l'action
    AdminLog.creer_log(
        admin=request.user,
        action_type=AdminLog.ActionType.SYSTEM_ACTION,
        description=f"Export des données météorologiques ({donnees.count()} relevés)",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return response


@admin_required
def modifier_station(request, station_id):
    """
    Modification d'une station existante
    """
    try:
        station = Station.objects.get(id=station_id)
    except Station.DoesNotExist:
        messages.error(request, "La station demandée n'existe pas.")
        return redirect('gestion_station')

    if request.method == 'POST':
        # Sauvegarder les anciennes données pour le log
        anciennes_donnees = {
            'nom': station.nom,
            'latitude': float(station.latitude),
            'longitude': float(station.longitude),
            'status': station.status,
            'energie': station.energie,
            'communication': station.communication,
            'capteurs': station.get_capteurs_disponibles()
        }

        # Mettre à jour la station
        station.nom = request.POST.get('nom', station.nom)
        station.latitude = request.POST.get('latitude', station.latitude)
        station.longitude = request.POST.get('longitude', station.longitude)
        station.energie = request.POST.get('energie', station.energie)
        station.communication = request.POST.get('communication', station.communication)
        station.status = request.POST.get('status', station.status)

        # Mettre à jour les capteurs
        station.capteur_temperature = 'capteur_temperature' in request.POST
        station.capteur_pression = 'capteur_pression' in request.POST
        station.capteur_vent = 'capteur_vent' in request.POST
        station.capteur_precipitation = 'capteur_precipitation' in request.POST
        station.capteur_ensoleillement = 'capteur_ensoleillement' in request.POST

        try:
            station.full_clean()  # Validation du modèle
            station.save()

            # Données après modification
            nouvelles_donnees = {
                'nom': station.nom,
                'latitude': float(station.latitude),
                'longitude': float(station.longitude),
                'status': station.status,
                'energie': station.energie,
                'communication': station.communication,
                'capteurs': station.get_capteurs_disponibles()
            }

            # Log de l'action
            AdminLog.creer_log(
                admin=request.user,
                action_type=AdminLog.ActionType.UPDATE_STATION,
                description=f"Modification de la station {station.nom}",
                station=station,
                donnees_avant=anciennes_donnees,
                donnees_apres=nouvelles_donnees,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Station {station.nom} modifiée avec succès !")
            return redirect('gestion_station')

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    # Préparer le contexte pour le formulaire
    context = {
        'title': f'Modifier {station.nom}',
        'station': station,
        'user': request.user,
        'form_data': {
            'nom': station.nom,
            'latitude': station.latitude,
            'longitude': station.longitude,
            'energie': station.energie,
            'communication': station.communication,
            'status': station.status,
            'capteur_temperature': station.capteur_temperature,
            'capteur_pression': station.capteur_pression,
            'capteur_vent': station.capteur_vent,
            'capteur_precipitation': station.capteur_precipitation,
            'capteur_ensoleillement': station.capteur_ensoleillement,
        }
    }

    return render(request, "modifier_station.html", context)


@admin_required
def supprimer_station(request, station_id):
    """
    Suppression d'une station
    """
    try:
        station = Station.objects.get(id=station_id)
    except Station.DoesNotExist:
        messages.error(request, "La station demandée n'existe pas.")
        return redirect('gestion_station')

    if request.method == 'POST':
        # Sauvegarder les données pour le log
        donnees_station = {
            'nom': station.nom,
            'latitude': float(station.latitude),
            'longitude': float(station.longitude),
            'status': station.status,
            'energie': station.energie,
            'communication': station.communication,
            'capteurs': station.get_capteurs_disponibles(),
            'nb_donnees': station.donnees_meteo.count()
        }

        nom_station = station.nom
        nb_donnees = station.donnees_meteo.count()

        # Supprimer la station (cela supprimera aussi les données météo associées via CASCADE)
        station.delete()

        # Log de l'action
        AdminLog.creer_log(
            admin=request.user,
            action_type=AdminLog.ActionType.DELETE_STATION,
            description=f"Suppression de la station {nom_station} ({nb_donnees} relevés supprimés)",
            donnees_avant=donnees_station,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f"Station {nom_station} supprimée avec succès !")
        return redirect('gestion_station')

    # Si ce n'est pas une requête POST, rediriger
    return redirect('gestion_station')


class SatelliteSimulator(threading.Thread):
    """Thread de simulation satellite"""

    def __init__(self):
        super().__init__()
        self.running = True
        self.daemon = True  # Thread démon qui s'arrête avec l'application

    def run(self):
        """Boucle principale de simulation"""
        print("🚀 Simulateur satellite démarré")

        while self.running:
            try:
                # Intervalle aléatoire 10-20 secondes
                time.sleep(random.uniform(10, 20))

                # Générer des données pour stations actives
                self.generate_data()

                # Événements aléatoires
                self.random_events()

            except Exception as e:
                print(f"Erreur simulateur: {e}")
                time.sleep(5)

    def generate_data(self):
        """Génère des données pour les stations actives"""
        active_stations = Station.objects.filter(status='ACTIF')

        for station in active_stations:
            data = {}

            if station.capteur_temperature:
                hour = timezone.now().hour
                if 6 <= hour <= 18:
                    base_temp = random.uniform(30, 45)
                else:
                    base_temp = random.uniform(20, 30)
                data['temperature'] = round(base_temp + random.uniform(-2, 2), 2)

            if station.capteur_pression:
                data['pression'] = round(1013 + random.uniform(-10, 10), 2)

            if station.capteur_vent:
                data['vitesse_vent'] = round(random.uniform(5, 25) + random.uniform(0, 10), 2)

            if station.capteur_precipitation:
                if random.random() < 0.05:
                    data['precipitation'] = round(random.uniform(0.1, 2.0), 2)
                else:
                    data['precipitation'] = 0.0

            if station.capteur_ensoleillement:
                hour = timezone.now().hour
                if 6 <= hour <= 18:
                    sunlight_base = random.uniform(800, 1000)
                    hour_factor = 1 - abs(12 - hour) / 6
                    sunlight = sunlight_base * hour_factor
                    data['ensoleillement'] = round(max(0, sunlight), 2)
                else:
                    data['ensoleillement'] = 0.0

            # Créer l'enregistrement
            WeatherData.objects.create(
                station=station,
                temperature=data.get('temperature'),
                pression=data.get('pression'),
                vitesse_vent=data.get('vitesse_vent'),
                precipitation=data.get('precipitation'),
                ensoleillement=data.get('ensoleillement'),
                timestamp=timezone.now()
            )

    def random_events(self):
        """Pannes et réparations aléatoires"""
        # Panne (1% de chance)
        if random.random() < 0.01:
            active_stations = Station.objects.filter(status='ACTIF')
            if active_stations:
                station = random.choice(list(active_stations))
                station.status = 'EN_PANNE'
                station.save()
                print(f"🚨 PANNE: {station.nom}")

        # Réparation (2% de chance) - seulement depuis MAINTENANCE
        if random.random() < 0.02:
            maintenance_stations = Station.objects.filter(status='MAINTENANCE')
            if maintenance_stations:
                station = random.choice(list(maintenance_stations))
                station.status = 'ACTIF'
                station.save()
                print(f"🔧 RÉPARATION: {station.nom}")

    def stop(self):
        """Arrête le simulateur"""
        self.running = False


# Variable globale pour le simulateur
simulator = None


def start_simulator():
    """Démarre le simulateur (à appeler une fois)"""
    global simulator
    if not simulator:
        simulator = SatelliteSimulator()
        simulator.start()
        return True
    return False


# Démarrer le simulateur au chargement de l'application
start_simulator()