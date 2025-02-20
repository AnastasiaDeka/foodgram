from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешает редактирование только автору рецепта.
    Чтение доступно всем пользователям.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True  # Разрешаем GET, HEAD, OPTIONS всем пользователям
        return obj.author == request.user  # Изменять и удалять может только автор


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """
    Разрешает редактирование только автору рецепта или администратору.
    Остальным пользователям — только чтение.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True  # Разрешаем чтение всем (GET, HEAD, OPTIONS)
        return request.user.is_staff or obj.author == request.user  # Только автор или админ

class IsAdminOrReadOnly(BasePermission):
    """
    Разрешает изменение объекта только администраторам.
    Остальным пользователям доступно только чтение.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Чтение доступно всем
        return request.user.is_staff  # Только админы могут изменять
