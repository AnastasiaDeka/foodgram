from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта"
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )
    
    password = models.CharField(
        max_length=128,
        verbose_name="Пароль"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
