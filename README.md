# DesertMet - Système d'Information Météorologique

## 📋 Description
Système de gestion des stations météorologiques pour zones sauvages isolées avec communication satellite.

## 🚀 Fonctionnalités

### 🔐 Authentification
- Connexion avec vérification domaine email (@DesertMet.com pour admins)
- Sessions de 48h
- Inscription bloquée pour emails admin

### 📡 Gestion des Stations
- 3 états : ACTIF, MAINTENANCE, EN_PANNE
- Capteurs configurables (température, pression, vent, précipitation, ensoleillement)
- Types d'énergie : Solaire, Batterie, Hybride
- Communication : Satellite, GSM, LoRa

### 📊 Données Météorologiques
- Collecte automatique via satellite
- Tableau de bord temps réel
- Filtrage par date et station
- Export TXT/CSV

### 🛠️ Administration
- Logs d'audit complète
- Surveillance système
- Modification/suppression stations
- Statistiques en temps réel

### 🛰️ Simulation Satellite
- Génération données toutes 10-20 secondes
- Simulation pannes/réparations
- Données réalistes selon capteurs

## 🏗️ Architecture

### Backend
- **Framework** : Django 4.2.0
- **Base de données** : PostgreSQL
- **Authentification** : Django Auth avec extension
- **Templates** : Django Templates

### Frontend
- **HTML/CSS/JS** vanilla
- **Rafraîchissement auto** : 15 secondes
- **Design responsive**

## 📁 Structure du Projet

DESERMET/
├── DesertMet/          # Configuration Django
├── users/             # Application principale
│   ├── migrations/    # Migrations DB
│   ├── static/        # CSS/JS
│   ├── templates/     # Templates HTML
│   ├── models.py      # Modèles DB
│   ├── views.py       # Logique métier
│   └── urls.py        # Routes
├── manage.py          # CLI Django
└── requirements.txt   # Dépendancespython -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

## 🛠️ Installation

### 1. Prérequis
```bash
Python 3.8+
PostgreSQL 12+
Redis (optionnel pour WebSockets)
```
### 2. Cloner le projet
```bash
git clone https://github.com/FOPATIDO/Station-M-t-orologique-sauvage.git
cd Station-M-t-orologique-sauvage
```
### 3. Environnement virtuel
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```
### 5. Configuration PostgreSQL
```sql
CREATE DATABASE desertmet_db;
CREATE USER desertmet_user WITH PASSWORD '2006';
GRANT ALL PRIVILEGES ON DATABASE desertmet_db TO desertmet_user;
```
### 6. Configuration Django
```bash
# Copier .env.example vers .env
cp .env.example .env
# Éditer .env avec vos informations
```
### 7. Migrations et superutilisateur
```bash
python manage.py migrate
python manage.py createsuperuser
# Email: admin@DesertMet.com
```
### 8. Lancer le serveur
```bash
python manage.py runserver
# Accès: http://localhost:8000
```
### 9.🧪 Données de test
Créer des stations
```bash
python manage.py shell
>>> from users.models import Station
>>> Station.objects.create(
...     nom="Sahara Nord",
...     latitude=23.456789,
...     longitude=-12.345678,
...     energie="SOLAIRE",
...     communication="SATELLITE",
...     status="ACTIF"
... )
```
### 10. Lancer la simulation
```bash
# Simulation automatique au démarrage
# OU
python manage.py simulate_satellite
```
### 10. 🔧 Commandes utiles
Développement
```bash
# Lancer le serveur
python manage.py runserver

# Créer migrations
python manage.py makemigrations users

# Appliquer migrations
python manage.py migrate

# Shell Django
python manage.py shell

# Tests
python manage.py test users
```
