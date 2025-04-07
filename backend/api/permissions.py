"""Права доступа для API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """Разрешает редактирование только автору рецепта или администратору.

    Остальным пользователям — только чтение.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на выполнение действия."""
        return request.method in SAFE_METHODS or (
            request.user == obj.author or request.user.is_staff
        )
