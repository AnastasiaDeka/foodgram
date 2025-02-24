from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser import views as djoser_views
from .views import RecipeViewSet, UserViewSet, IngredientViewSet
from tags.views import TagViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # Ваши обычные маршруты
    path('', include(router.urls)),

    # Кастомный маршрут для подписки/отписки
    path('auth/', include('djoser.urls')),
    path('auth/token/', include('djoser.urls.authtoken')), 
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
]
