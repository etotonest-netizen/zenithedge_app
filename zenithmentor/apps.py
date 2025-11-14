from django.apps import AppConfig


class ZenithmentorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zenithmentor'
    verbose_name = 'ZenithMentor Training System'
    
    def ready(self):
        """Initialize ML models and scenario bank on startup."""
        pass
