from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.users"
    label = "users"

    def ready(self) -> None:
        from modules.users import signals  # noqa: F401
