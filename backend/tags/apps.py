"""Настройки приложения для работы с тегами."""

from django.apps import AppConfig


class TagsConfig(AppConfig):
    """Конфигурация приложения для работы с тегами."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tags'
