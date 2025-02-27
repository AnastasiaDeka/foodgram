"""Маршруты для API проекта Foodgram.

Этот модуль определяет маршруты для работы с рецептами, пользователями,
ингредиентами и тегами. Также подключены маршруты Djoser для аутентификации.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet,
    UserViewSet,
    IngredientViewSet,
)
from tags.views import TagViewSet

app_name = "api"

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", UserViewSet, basename="users")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("tags", TagViewSet, basename="tags")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("users/me/", UserViewSet.as_view({"get": "me"}), name="user-me"),
]
