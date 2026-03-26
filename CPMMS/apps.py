from django.apps import AppConfig


class CpmmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CPMMS'

    def ready(self):
        import CPMMS.signals 
