"""
users/management/commands/simulate_satellite.py
Script de simulation de réception satellite des données météorologiques
"""

import time
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from users.models import Station, WeatherData
import logging

# Configuration du logger
logger = logging.getLogger('satellite_simulator')


class Command(BaseCommand):
    help = 'Simule la réception satellite des données météorologiques'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=15,
            help='Intervalle moyen entre les transmissions en secondes (défaut: 15)'
        )
        parser.add_argument(
            '--max-stations',
            type=int,
            default=None,
            help='Nombre maximum de stations à simuler (défaut: toutes)'
        )
        parser.add_argument(
            '--run-time',
            type=int,
            default=None,
            help='Durée d\'exécution en secondes (défaut: infini)'
        )

    def handle(self, *args, **options):
        """
        Point d'entrée de la commande
        """
        interval = options['interval']
        max_stations = options['max_stations']
        run_time = options['run_time']

        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Démarrage du simulateur satellite DesertMet\n'
                f'📡 Intervalle: {interval}s | Mode: {"Test" if max_stations else "Production"}'
            )
        )

        start_time = timezone.now()
        transmission_count = 0
        error_count = 0

        try:
            while True:
                # Vérifier si on a dépassé le temps d'exécution
                if run_time and (timezone.now() - start_time).seconds >= run_time:
                    self.stdout.write(
                        self.style.WARNING('⏱️  Temps d\'exécution écoulé')
                    )
                    break

                try:
                    # Générer des données pour les stations
                    transmissions = self.generate_satellite_data(max_stations)

                    if transmissions:
                        # Afficher le résumé
                        self.display_transmission_summary(transmissions)
                        transmission_count += len(transmissions)

                    # Simuler des pannes/réparations aléatoires
                    self.simulate_random_events()

                    # Attendre un intervalle aléatoire entre 10 et 20 secondes
                    sleep_time = random.uniform(10, 20)
                    time.sleep(sleep_time)

                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('\n🛑 Simulation interrompue par l\'utilisateur'))
                    break
                except Exception as e:
                    error_count += 1
                    logger.error(f"Erreur lors de la transmission: {str(e)}")
                    if error_count > 10:
                        self.stdout.write(
                            self.style.ERROR('❌ Trop d\'erreurs, arrêt du simulateur')
                        )
                        break
                    time.sleep(5)  # Attendre avant de réessayer

            # Statistiques finales
            self.display_final_stats(start_time, transmission_count, error_count)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur fatale: {str(e)}'))

    def generate_satellite_data(self, max_stations=None):
        """
        Génère des données pour les stations actives
        Règle métier: Seules les stations ACTIF génèrent des données
        """
        # Récupérer les stations ACTIVES
        active_stations = Station.objects.filter(status='ACTIF')

        if max_stations:
            active_stations = active_stations[:max_stations]

        transmissions = []

        for station in active_stations:
            try:
                # Générer des données selon les capteurs disponibles
                weather_data = self.generate_station_data(station)

                if weather_data:
                    # Sauvegarder dans la base de données
                    with transaction.atomic():
                        weather_obj = WeatherData.objects.create(
                            station=station,
                            temperature=weather_data.get('temperature'),
                            pression=weather_data.get('pression'),
                            vitesse_vent=weather_data.get('vitesse_vent'),
                            precipitation=weather_data.get('precipitation'),
                            ensoleillement=weather_data.get('ensoleillement'),
                            timestamp=timezone.now()
                        )

                    transmissions.append({
                        'station': station.nom,
                        'data': weather_data,
                        'success': True
                    })

            except Exception as e:
                logger.error(f"Erreur génération données station {station.nom}: {str(e)}")
                transmissions.append({
                    'station': station.nom,
                    'error': str(e),
                    'success': False
                })

        return transmissions

    def generate_station_data(self, station):
        """
        Génère des données météorologiques réalistes selon les capteurs disponibles
        """
        data = {}

        # Température (réaliste pour le désert)
        if station.capteur_temperature:
            # Variation réaliste: 20-45°C la journée, plus frais la nuit
            hour = timezone.now().hour
            if 6 <= hour <= 18:  # Jour
                base_temp = random.uniform(30, 45)
            else:  # Nuit
                base_temp = random.uniform(20, 30)

            # Variation aléatoire
            variation = random.uniform(-2, 2)
            data['temperature'] = round(base_temp + variation, 2)

        # Pression atmosphérique
        if station.capteur_pression:
            # Pression normale ~1013 hPa, variation ±10 hPa
            base_pression = 1013
            variation = random.uniform(-10, 10)
            data['pression'] = round(base_pression + variation, 2)

        # Vitesse du vent
        if station.capteur_vent:
            # Vent dans le désert: généralement faible à modéré
            base_vent = random.uniform(5, 25)  # km/h
            rafale = random.uniform(0, 10)  # rafales
            data['vitesse_vent'] = round(base_vent + rafale, 2)

        # Précipitations (très rares dans le désert)
        if station.capteur_precipitation:
            # 95% de chance de 0mm, 5% de chance de très faible pluie
            if random.random() < 0.05:
                data['precipitation'] = round(random.uniform(0.1, 2.0), 2)
            else:
                data['precipitation'] = 0.0

        # Ensoleillement
        if station.capteur_ensoleillement:
            hour = timezone.now().hour
            if 6 <= hour <= 18:  # Jour
                # Rayonnement solaire maximal ~1000 W/m²
                sunlight_base = random.uniform(800, 1000)

                # Variation selon l'heure
                hour_factor = 1 - abs(12 - hour) / 6  # Maximum à midi
                sunlight = sunlight_base * hour_factor
                data['ensoleillement'] = round(max(0, sunlight), 2)
            else:  # Nuit
                data['ensoleillement'] = 0.0

        return data

    def simulate_random_events(self):
        """
        Simule des événements aléatoires: pannes et réparations
        """
        # 1% de chance qu'une station ACTIF passe en panne
        if random.random() < 0.01:
            self.simulate_panne()

        # 2% de chance qu'une station MAINTENANCE soit réparée
        if random.random() < 0.02:
            self.simulate_reparation()

    def simulate_panne(self):
        """
        Simule une panne sur une station ACTIVE
        """
        try:
            # Trouver une station ACTIVE aléatoire
            active_stations = Station.objects.filter(status='ACTIF')
            if not active_stations:
                return

            station = random.choice(active_stations)

            # Sauvegarder l'ancien statut
            ancien_statut = station.status

            # Passer en panne
            station.status = 'EN_PANNE'
            station.save()

            # Log de l'événement
            logger.info(f"🚨 PANNE SIMULÉE: Station {station.nom} est passée de {ancien_statut} à EN_PANNE")

            self.stdout.write(
                self.style.ERROR(f'🚨 PANNE: Station {station.nom} est hors service')
            )

        except Exception as e:
            logger.error(f"Erreur simulation panne: {str(e)}")

    def simulate_reparation(self):
        """
        Simule la réparation d'une station MAINTENANCE
        Règle: Seulement si elle était déjà en MAINTENANCE
        """
        try:
            # Trouver une station MAINTENANCE aléatoire
            maintenance_stations = Station.objects.filter(status='MAINTENANCE')
            if not maintenance_stations:
                return

            station = random.choice(maintenance_stations)

            # Sauvegarder l'ancien statut
            ancien_statut = station.status

            # Réparer (passer à ACTIF)
            station.status = 'ACTIF'
            station.save()

            # Log de l'événement
            logger.info(f"🔧 RÉPARATION SIMULÉE: Station {station.nom} est passée de {ancien_statut} à ACTIF")

            self.stdout.write(
                self.style.SUCCESS(f'🔧 RÉPARATION: Station {station.nom} est de nouveau opérationnelle')
            )

        except Exception as e:
            logger.error(f"Erreur simulation réparation: {str(e)}")

    def display_transmission_summary(self, transmissions):
        """
        Affiche un résumé des transmissions
        """
        successful = [t for t in transmissions if t['success']]
        failed = [t for t in transmissions if not t['success']]

        if successful:
            # Afficher les 3 premières transmissions réussies
            display_count = min(3, len(successful))
            for i in range(display_count):
                trans = successful[i]
                station = trans['station']
                data = trans['data']

                # Formater les données
                data_str = []
                if 'temperature' in data:
                    data_str.append(f"{data['temperature']}°C")
                if 'vitesse_vent' in data:
                    data_str.append(f"{data['vitesse_vent']}km/h")
                if 'pression' in data:
                    data_str.append(f"{data['pression']}hPa")

                self.stdout.write(
                    f"📡 {station}: {', '.join(data_str)}"
                )

            if len(successful) > display_count:
                self.stdout.write(f"   ... et {len(successful) - display_count} autres stations")

        if failed:
            self.stdout.write(
                self.style.WARNING(f"⚠️  {len(failed)} échecs de transmission")
            )

    def display_final_stats(self, start_time, transmission_count, error_count):
        """
        Affiche les statistiques finales
        """
        duration = timezone.now() - start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("📊 STATISTIQUES DE SIMULATION"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"⏱️  Durée: {hours}h {minutes}m {seconds}s")
        self.stdout.write(f"📨 Transmissions réussies: {transmission_count}")
        self.stdout.write(f"❌ Erreurs: {error_count}")

        if transmission_count > 0:
            avg_interval = duration.seconds / transmission_count if transmission_count > 0 else 0
            self.stdout.write(f"📈 Intervalle moyen: {avg_interval:.1f}s par station")

        # Statistiques des stations
        total_stations = Station.objects.count()
        active_stations = Station.objects.filter(status='ACTIF').count()
        maintenance_stations = Station.objects.filter(status='MAINTENANCE').count()
        panne_stations = Station.objects.filter(status='EN_PANNE').count()

        self.stdout.write(f"\n🏭 ÉTAT DU PARC:")
        self.stdout.write(f"   Total: {total_stations} stations")
        self.stdout.write(f"   ✅ Actives: {active_stations}")
        self.stdout.write(f"   🔧 Maintenance: {maintenance_stations}")
        self.stdout.write(f"   🚨 En panne: {panne_stations}")
        self.stdout.write("=" * 50)