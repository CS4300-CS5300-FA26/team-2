from django.apps import AppConfig


class AiIntelligenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_intelligence"
    
    # Import signals
    # From django docs: "Subclasses can override this method to perform initialization tasks such as registering signals."
    def ready(self):
        from . import signals