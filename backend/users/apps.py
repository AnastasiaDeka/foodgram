"""Конфигурация приложения для работы с пользователями."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения 'users'."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
