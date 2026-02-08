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
└── requirements.txt   # Dépendances

## 🛠️ Installation

### 1. Prérequis
```bash
Python 3.8+
PostgreSQL 12+
Redis (optionnel pour WebSockets)
