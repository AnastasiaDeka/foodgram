"""Модели для тегов."""

from django.db import models


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name
