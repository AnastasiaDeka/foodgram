from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser import views as djoser_views
from .views import RecipeViewSet, UserViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Маршруты для авторизации через Djoser
    path('auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    

  # Обработает регистрацию, восстановление пароля и прочее
    

    # Основные маршруты приложения
    path('', include(router.urls)),
]
