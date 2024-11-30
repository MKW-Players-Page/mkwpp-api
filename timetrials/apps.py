from django.apps import AppConfig


class TimetrialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timetrials'

    def ready(self):
        import timetrials.signals  # noqa: F401
