"""
users/models.py
Modèles de base de données pour l'application DesertMet
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# ==============================================
# MODÈLES DES UTILISATEURS
# ==============================================

class UserManager(BaseUserManager):
    """Gestionnaire personnalisé pour le modèle User"""

    def create_user(self, email, fullname, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe
        """
        if not email:
            raise ValueError('L\'email est obligatoire')

        email = self.normalize_email(email)
        user = self.model(email=email, fullname=fullname, **extra_fields)
        user.set_password(password)  # Hachage automatique du mot de passe
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, fullname, password, **extra_fields)


class User(AbstractUser):
    """
    Modèle utilisateur étendu avec des champs personnalisés
    Chaque utilisateur a un mot de passe (géré par Django)
    """

    # On retire le champ username par défaut, on utilisera l'email
    username = None

    # Champs obligatoires
    email = models.EmailField(
        verbose_name='Adresse email',
        max_length=255,
        unique=True,
        help_text='Email unique pour la connexion'
    )

    fullname = models.CharField(
        verbose_name='Nom complet',
        max_length=100,
        help_text='Nom et prénom de l\'utilisateur'
    )

    # Rôle utilisateur
    is_desert_admin = models.BooleanField(
        verbose_name='Administrateur DesertMet',
        default=False,
        help_text='Cocher si l\'utilisateur est un administrateur gouvernemental'
    )

    # Date de création
    date_joined = models.DateTimeField(
        verbose_name='Date d\'inscription',
        default=timezone.now
    )

    # Configuration pour utiliser l'email comme identifiant
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']  # fullname requis lors de la création

    objects = UserManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.fullname} ({self.email})"

    def is_admin(self):
        """
        Vérifie si l'utilisateur est un admin DesertMet
        Basé sur le domaine de l'email ET le champ booléen
        """
        return self.email.endswith('@DesertMet.com') and self.is_desert_admin


# ==============================================
# MODÈLES DES STATIONS MÉTÉOROLOGIQUES
# ==============================================

class Station(models.Model):
    """
    Modèle représentant une station météorologique autonome
    """

    # Énumération des types d'énergie
    class EnergyType(models.TextChoices):
        SOLAIRE = 'SOLAIRE', 'Solaire'
        BATTERIE = 'BATTERIE', 'Batterie'
        HYBRIDE = 'HYBRIDE', 'Hybride (Solaire + Batterie)'

    # Énumération des types de communication
    class CommunicationType(models.TextChoices):
        SATELLITE = 'SATELLITE', 'Satellite'
        GSM = 'GSM', 'Réseau GSM'
        LORA = 'LORA', 'LoRa'

    # Énumération des états de fonctionnement (CRUCIAL)
    class Status(models.TextChoices):
        ACTIF = 'ACTIF', 'Actif'
        MAINTENANCE = 'MAINTENANCE', 'En maintenance'
        EN_PANNE = 'EN_PANNE', 'En panne'

    # Identifiant unique
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID unique'
    )

    # Informations de base
    nom = models.CharField(
        verbose_name='Nom de la station',
        max_length=100,
        unique=True,
        help_text='Nom unique identifiant la station'
    )

    # Localisation GPS
    latitude = models.DecimalField(
        verbose_name='Latitude',
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Coordonnée GPS : -90 à +90'
    )

    longitude = models.DecimalField(
        verbose_name='Longitude',
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text='Coordonnée GPS : -180 à +180'
    )

    # Configuration technique
    energie = models.CharField(
        verbose_name='Source d\'énergie',
        max_length=20,
        choices=EnergyType.choices,
        default=EnergyType.SOLAIRE,
        help_text='Type de source d\'énergie'
    )

    communication = models.CharField(
        verbose_name='Type de communication',
        max_length=20,
        choices=CommunicationType.choices,
        default=CommunicationType.SATELLITE,
        help_text='Méthode de transmission des données'
    )

    # État de fonctionnement (CHAMP CRUCIAL)
    status = models.CharField(
        verbose_name='État de la station',
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIF,
        help_text='État actuel de fonctionnement'
    )

    # Configuration des capteurs disponibles
    capteur_temperature = models.BooleanField(
        verbose_name='Capteur de température',
        default=True,
        help_text='La station possède-t-elle un capteur de température ?'
    )

    capteur_pression = models.BooleanField(
        verbose_name='Capteur de pression',
        default=True,
        help_text='La station possède-t-elle un capteur de pression ?'
    )

    capteur_vent = models.BooleanField(
        verbose_name='Capteur de vent',
        default=True,
        help_text='La station possède-t-elle un capteur de vent ?'
    )

    capteur_ensoleillement = models.BooleanField(
        verbose_name='Capteur d\'ensoleillement',
        default=True,
        help_text='La station possède-t-elle un capteur d\'ensoleillement ?'
    )

    capteur_precipitation = models.BooleanField(
        verbose_name='Capteur de précipitation',
        default=True,
        help_text='La station possède-t-elle un capteur de précipitation ?'
    )

    # Informations de suivi
    date_creation = models.DateTimeField(
        verbose_name='Date de création',
        auto_now_add=True
    )

    date_mise_a_jour = models.DateTimeField(
        verbose_name='Dernière mise à jour',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Station météorologique'
        verbose_name_plural = 'Stations météorologiques'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_status_display()})"

    def get_localisation(self):
        """Retourne la localisation GPS formatée"""
        return f"Lat: {self.latitude}, Lon: {self.longitude}"

    def get_capteurs_disponibles(self):
        """Retourne la liste des capteurs disponibles"""
        capteurs = []
        if self.capteur_temperature:
            capteurs.append('Température')
        if self.capteur_pression:
            capteurs.append('Pression')
        if self.capteur_vent:
            capteurs.append('Vent')
        if self.capteur_ensoleillement:
            capteurs.append('Ensoleillement')
        if self.capteur_precipitation:
            capteurs.append('Précipitation')
        return capteurs

    def peut_generer_donnees(self):
        """
        Vérifie si la station peut générer des données
        RÈGLE MÉTIER : Une station ne génère des données que si status == ACTIF
        """
        return self.status == Station.Status.ACTIF


# ==============================================
# MODÈLES DES DONNÉES MÉTÉOROLOGIQUES
# ==============================================

class WeatherData(models.Model):
    """
    Modèle stockant les données météorologiques envoyées par les stations
    """

    # Relation avec la station (clé étrangère)
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='donnees_meteo',
        verbose_name='Station émettrice',
        help_text='Station qui a généré ces données'
    )

    # Données météorologiques (peuvent être nulles si capteur non disponible)
    temperature = models.DecimalField(
        verbose_name='Température (°C)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Température en degrés Celsius'
    )

    pression = models.DecimalField(
        verbose_name='Pression atmosphérique (hPa)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Pression en hectopascals'
    )

    vitesse_vent = models.DecimalField(
        verbose_name='Vitesse du vent (km/h)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Vitesse du vent en kilomètres par heure'
    )

    precipitation = models.DecimalField(
        verbose_name='Précipitations (mm)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Quantité de pluie en millimètres'
    )

    ensoleillement = models.DecimalField(
        verbose_name='Ensoleillement (W/m²)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Rayonnement solaire en watts par mètre carré'
    )

    # Horodatage précis
    timestamp = models.DateTimeField(
        verbose_name='Date et heure du relevé',
        default=timezone.now,
        help_text='Moment exact où les données ont été collectées'
    )

    # Métadonnées
    date_reception = models.DateTimeField(
        verbose_name='Date de réception',
        auto_now_add=True,
        help_text='Date à laquelle le système a reçu ces données'
    )

    class Meta:
        verbose_name = 'Donnée météorologique'
        verbose_name_plural = 'Données météorologiques'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['station', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Données de {self.station.nom} à {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def est_complet(self):
        """
        Vérifie si toutes les données sont présentes
        (selon les capteurs disponibles sur la station)
        """
        if self.station.capteur_temperature and self.temperature is None:
            return False
        if self.station.capteur_pression and self.pression is None:
            return False
        if self.station.capteur_vent and self.vitesse_vent is None:
            return False
        if self.station.capteur_precipitation and self.precipitation is None:
            return False
        if self.station.capteur_ensoleillement and self.ensoleillement is None:
            return False
        return True


# ==============================================
# MODÈLES DE TRAÇABILITÉ (LOGS ADMIN)
# ==============================================

class AdminLog(models.Model):
    """
    Modèle pour enregistrer toutes les actions des administrateurs
    Garantit l'auditabilité du système
    """

    # Types d'actions possibles
    class ActionType(models.TextChoices):
        CREATE_STATION = 'CREATE_STATION', 'Création de station'
        UPDATE_STATION = 'UPDATE_STATION', 'Modification de station'
        DELETE_STATION = 'DELETE_STATION', 'Suppression de station'
        CHANGE_STATUS = 'CHANGE_STATUS', 'Changement de statut'
        UPDATE_PARAMETERS = 'UPDATE_PARAMETERS', 'Modification de paramètres'
        USER_MANAGEMENT = 'USER_MANAGEMENT', 'Gestion utilisateur'
        SYSTEM_ACTION = 'SYSTEM_ACTION', 'Action système'

    # Identifiant unique
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Qui a fait l'action
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_admin',
        verbose_name='Administrateur',
        help_text='Administrateur ayant effectué l\'action'
    )

    # Quelle action
    action_type = models.CharField(
        verbose_name='Type d\'action',
        max_length=50,
        choices=ActionType.choices,
        help_text='Catégorie de l\'action effectuée'
    )

    # Description détaillée
    description = models.TextField(
        verbose_name='Description',
        help_text='Description détaillée de l\'action effectuée'
    )

    # Données avant/après (pour audit)
    donnees_avant = models.JSONField(
        verbose_name='Données avant modification',
        null=True,
        blank=True,
        help_text='État des données avant l\'action (format JSON)'
    )

    donnees_apres = models.JSONField(
        verbose_name='Données après modification',
        null=True,
        blank=True,
        help_text='État des données après l\'action (format JSON)'
    )

    # Cible de l'action (si applicable)
    station_concerne = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_station',
        verbose_name='Station concernée',
        help_text='Station affectée par cette action (si applicable)'
    )

    utilisateur_concerne = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_utilisateur',
        verbose_name='Utilisateur concerné',
        help_text='Utilisateur affecté par cette action (si applicable)'
    )

    # Horodatage
    timestamp = models.DateTimeField(
        verbose_name='Date et heure',
        auto_now_add=True,
        help_text='Moment exact de l\'action'
    )

    # Adresse IP (pour sécurité)
    ip_address = models.GenericIPAddressField(
        verbose_name='Adresse IP',
        null=True,
        blank=True,
        help_text='Adresse IP de l\'administrateur au moment de l\'action'
    )

    class Meta:
        verbose_name = 'Log administrateur'
        verbose_name_plural = 'Logs administrateurs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin', 'timestamp']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} par {self.admin} à {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def creer_log(admin, action_type, description, **kwargs):
        """
        Méthode utilitaire pour créer facilement un log
        """
        return AdminLog.objects.create(
            admin=admin,
            action_type=action_type,
            description=description,
            station_concerne=kwargs.get('station'),
            utilisateur_concerne=kwargs.get('utilisateur'),
            donnees_avant=kwargs.get('donnees_avant'),
            donnees_apres=kwargs.get('donnees_apres'),
            ip_address=kwargs.get('ip_address')
        )