from django.apps import AppConfig


class VacationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vacation"

    def ready(self):
        import vacation.models  # Ensure the signal is imported
