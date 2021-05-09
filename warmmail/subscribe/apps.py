from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SubscribeConfig(AppConfig):
    name = "warmmail.subscribe"
    verbose_name = _("Subscribe")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        try:
            import warmmail.subscribe.signals  # noqa F401
        except ImportError:
            pass
