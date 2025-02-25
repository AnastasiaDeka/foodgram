from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser import views as djoser_views
from .views import RecipeViewSet, UserViewSet, IngredientViewSet
from tags.views import TagViewSet

# Регистрация маршрутов для API
router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'cart', RecipeViewSet, basename='cart')

# Добавляем новый маршрут для корзины
urlpatterns = [
    # Ваши обычные маршруты
    path('', include(router.urls)),

    # Логирование каждого запроса
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),

]
