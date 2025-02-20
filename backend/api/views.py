from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Favorite, ShoppingCart, Recipe
from users.models import User
from .pagination import PaginatorWithLimit
from .serializers import (
    UserSerializer, UserUpdateSerializer, UserProfileSerializer,
    RecipeSerializer, RecipeCreateUpdateSerializer, 
    SubscriptionSerializer
)
from .serializers import UserCreateSerializer
from .filters import RecipeFilter
from .permissions import IsAuthorOrAdminOrReadOnly

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами с фильтрацией."""
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    pagination_class = PaginatorWithLimit

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохранение рецепта с указанием автора."""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Фильтрация рецептов с учетом пользователя."""
        queryset = super().get_queryset()
        user = self.request.user

        if self.request.query_params.get('is_favorited') == '1' and user.is_authenticated:
            queryset = queryset.filter(favorite__user=user)

        if self.request.query_params.get('is_in_shopping_cart') == '1' and user.is_authenticated:
            queryset = queryset.filter(shoppingcart__user=user)

        return queryset

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт в/из избранного."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            # Добавление в избранное
            favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({"detail": "Recipe added to favorites"}, status=status.HTTP_201_CREATED)
            return Response({"detail": "Recipe already in favorites"}, status=status.HTTP_200_OK)

        # Удаление из избранного
        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response({"detail": "Recipe removed from favorites"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт в/из корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            # Добавление в корзину
            shopping_cart, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({"detail": "Recipe added to shopping cart"}, status=status.HTTP_201_CREATED)
            return Response({"detail": "Recipe already in shopping cart"}, status=status.HTTP_200_OK)

        # Удаление из корзины
        shopping_cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        shopping_cart.delete()
        return Response({"detail": "Recipe removed from shopping cart"}, status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""
    queryset = User.objects.all().order_by('email')
    pagination_class = PaginatorWithLimit
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода запроса."""
        if self.action == "me":
            return UserProfileSerializer
        if self.request.method == "GET":
            return UserSerializer
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserUpdateSerializer

    def get_permissions(self):
        """Назначение прав доступа в зависимости от экшена."""
        print(f"Проверка токена: {self.request.auth}")
        if self.action in ("me", "subscriptions", "subscribe"):
            return [IsAuthenticated()]
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение данных текущего пользователя."""
        print(f"Запрос от пользователя: {request.user}")
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка и отписка от автора."""
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'author': author.id}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(Subscription, user=request.user, author=author).delete()
        return Response({'detail': 'Отписка прошла успешно'}, status=status.HTTP_204_NO_CONTENT)


