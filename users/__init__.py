# users/__init__.py
default_app_config = 'users.apps.UsersConfig'

# Démarrer le simulateur quand Django démarre
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def start_simulation(sender, **kwargs):
    from .views import start_simulator
    start_simulator()


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Démarrer le simulateur après les migrations
        post_migrate.connect(start_simulation, sender=self)