# users/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Station, WeatherData
from django.utils import timezone
import random
from datetime import datetime


class SatelliteDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.simulation_task = None

        # Démarrer la simulation quand un client se connecte
        self.simulation_task = asyncio.create_task(self.run_simulation())

    async def disconnect(self, close_code):
        # Arrêter la simulation à la déconnexion
        if self.simulation_task:
            self.simulation_task.cancel()

    async def receive(self, text_data):
        # Recevoir des messages du client
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'get_initial_data':
            # Envoyer les données initiales
            stations_data = await self.get_stations_data()
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': stations_data
            }))

    async def run_simulation(self):
        """Exécute la simulation en boucle"""
        while True:
            try:
                # Attendre un intervalle aléatoire (10-20 secondes)
                await asyncio.sleep(random.uniform(10, 20))

                # Générer de nouvelles données
                new_data = await self.generate_satellite_data()

                # Envoyer les nouvelles données à tous les clients
                await self.send(text_data=json.dumps({
                    'type': 'new_data',
                    'data': new_data,
                    'timestamp': timezone.now().isoformat()
                }))

                # Simuler des événements aléatoires
                await self.simulate_random_events()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erreur simulation: {e}")
                await asyncio.sleep(5)

    @database_sync_to_async
    def get_stations_data(self):
        """Récupère les données actuelles des stations"""
        stations = Station.objects.all()
        data = []

        for station in stations:
            last_data = WeatherData.objects.filter(
                station=station
            ).order_by('-timestamp').first()

            data.append({
                'id': str(station.id),
                'name': station.nom,
                'status': station.status,
                'latitude': float(station.latitude),
                'longitude': float(station.longitude),
                'sensors': {
                    'temperature': station.capteur_temperature,
                    'pressure': station.capteur_pression,
                    'wind': station.capteur_vent,
                    'precipitation': station.capteur_precipitation,
                    'sunshine': station.capteur_ensoleillement,
                },
                'last_data': {
                    'temperature': float(last_data.temperature) if last_data and last_data.temperature else None,
                    'pressure': float(last_data.pression) if last_data and last_data.pression else None,
                    'wind': float(last_data.vitesse_vent) if last_data and last_data.vitesse_vent else None,
                    'precipitation': float(last_data.precipitation) if last_data and last_data.precipitation else None,
                    'sunshine': float(last_data.ensoleillement) if last_data and last_data.ensoleillement else None,
                    'timestamp': last_data.timestamp.isoformat() if last_data else None,
                } if last_data else None
            })

        return data

    @database_sync_to_async
    def generate_satellite_data(self):
        """Génère de nouvelles données pour les stations actives"""
        active_stations = Station.objects.filter(status='ACTIF')
        new_data = []

        for station in active_stations:
            # Générer des données selon les capteurs
            weather_data = {}

            if station.capteur_temperature:
                hour = timezone.now().hour
                if 6 <= hour <= 18:
                    base_temp = random.uniform(30, 45)
                else:
                    base_temp = random.uniform(20, 30)
                weather_data['temperature'] = round(base_temp + random.uniform(-2, 2), 2)

            if station.capteur_pression:
                weather_data['pressure'] = round(1013 + random.uniform(-10, 10), 2)

            if station.capteur_vent:
                weather_data['wind'] = round(random.uniform(5, 25) + random.uniform(0, 10), 2)

            if station.capteur_precipitation:
                if random.random() < 0.05:
                    weather_data['precipitation'] = round(random.uniform(0.1, 2.0), 2)
                else:
                    weather_data['precipitation'] = 0.0

            if station.capteur_ensoleillement:
                hour = timezone.now().hour
                if 6 <= hour <= 18:
                    sunlight_base = random.uniform(800, 1000)
                    hour_factor = 1 - abs(12 - hour) / 6
                    sunlight = sunlight_base * hour_factor
                    weather_data['sunshine'] = round(max(0, sunlight), 2)
                else:
                    weather_data['sunshine'] = 0.0

            # Sauvegarder dans la base
            WeatherData.objects.create(
                station=station,
                temperature=weather_data.get('temperature'),
                pression=weather_data.get('pressure'),
                vitesse_vent=weather_data.get('wind'),
                precipitation=weather_data.get('precipitation'),
                ensoleillement=weather_data.get('sunshine'),
                timestamp=timezone.now()
            )

            new_data.append({
                'station_id': str(station.id),
                'station_name': station.nom,
                'data': weather_data,
                'timestamp': timezone.now().isoformat()
            })

        return new_data

    @database_sync_to_async
    def simulate_random_events(self):
        """Simule pannes et réparations"""
        # Panne aléatoire (1% de chance)
        if random.random() < 0.01:
            active_stations = Station.objects.filter(status='ACTIF')
            if active_stations:
                station = random.choice(list(active_stations))
                station.status = 'EN_PANNE'
                station.save()

        # Réparation aléatoire (2% de chance)
        if random.random() < 0.02:
            maintenance_stations = Station.objects.filter(status='MAINTENANCE')
            if maintenance_stations:
                station = random.choice(list(maintenance_stations))
                station.status = 'ACTIF'
                station.save()