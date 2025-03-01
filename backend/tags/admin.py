"""Административная часть для тегов."""

from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    """Админ-класс для модели Tag."""

    search_fields = ('name',)
    list_display = ('name', 'slug')


admin.site.register(Tag, TagAdmin)
