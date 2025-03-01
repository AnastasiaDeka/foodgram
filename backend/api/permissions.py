"""Права доступа для API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает редактирование только автору рецепта.

    Чтение доступно всем пользователям.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на выполнение действия."""
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """Разрешает редактирование только автору рецепта или администратору.

    Остальным пользователям — только чтение.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на выполнение действия."""
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or obj.author == request.user


class IsAdminOrReadOnly(BasePermission):
    """Разрешает изменение объекта только администраторам.

    Остальным пользователям доступно только чтение.
    """

    def has_permission(self, request, view):
        """Проверяет наличие прав на выполнение действия."""
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff
