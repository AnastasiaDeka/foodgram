"""Модуль с маршрутизацией для пользователей."""

from api.views import UserViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
