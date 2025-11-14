from django.apps import AppConfig


class PropcoachConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'propcoach'
    verbose_name = 'Prop Firm Training Coach'
    
    def ready(self):
        """Initialize app"""
        import propcoach.signals  # noqa
