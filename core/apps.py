"""
App configuration for the core application.

This module defines the configuration class for the core Django app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """Configuration class for the core application."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "core"
    verbose_name: str = _("Core")

    def ready(self) -> None:
        """Perform initialization when the app is ready.

        This method is called when the application is ready and is used
        to import signal handlers to ensure they are registered.
        """
        import core.signals  # noqa: F401
