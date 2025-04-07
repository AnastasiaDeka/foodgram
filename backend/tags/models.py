"""Модели для тегов."""

from api.constants import MAX_SLUG_LENGTH, MAX_TAG_NAME_LENGTH
from django.db import models


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(max_length=MAX_TAG_NAME_LENGTH, unique=True)
    slug = models.SlugField(unique=True, max_length=MAX_SLUG_LENGTH)

    def __str__(self):
        """Возвращает строковое представление тега."""
        return f"Tag: {self.name} (ID: {self.id})"
