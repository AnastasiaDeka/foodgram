"""Модуль, содержащий модели для работы с пользователями."""

from api.constants import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Модель пользователя с расширенными полями.

    Наследуется от AbstractUser и добавляет дополнительные поля:
    email, first_name, last_name, avatar.
    """

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name="Электронная почта"
    )
    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        """Метаданные модели User."""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        """
        Возвращает строковое представление пользователя.

        Returns:
            str: Имя пользователя
        """
        return self.username
