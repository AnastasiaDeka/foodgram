from rest_framework import status, permissions, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
import django_filters
from rest_framework.exceptions import NotFound
from recipes.models import Favorite, ShoppingCart, Recipe, RecipeIngredient, Ingredient, Subscription
from users.models import User
from .pagination import PaginatorWithLimit
from .serializers import (
    UserSerializer, UserUpdateSerializer, UserProfileSerializer,
    RecipeSerializer, RecipeCreateUpdateSerializer, 
    SubscriptionSerializer, SetPasswordSerializer, IngredientSerializer, 
    AvatarUpdateSerializer, IngredientAmountSerializer
)
from .serializers import UserCreateSerializer
from .filters import RecipeFilter, IngredientSearchFilter
from .permissions import IsAuthorOrAdminOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода запроса."""
        if self.action == 'me':
            return UserProfileSerializer
        if self.request.method == 'GET':
            return UserSerializer
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserUpdateSerializer

    def get_permissions(self):
        """Назначение прав доступа в зависимости от экшена."""
        if self.action in ('me', 'subscriptions', 'subscribe'):
            return [IsAuthenticated()]
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()
        
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Регистрация нового пользователя."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение данных текущего пользователя."""
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        queryset = Subscription.objects.filter(user=request.user)

        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка и отписка от автора."""

        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if Subscription.objects.filter(user=request.user, subscribed_user=author).exists():
                return Response({'detail': 'Вы уже подписаны'}, status=status.HTTP_400_BAD_REQUEST)

            subscription = Subscription.objects.create(user=request.user, subscribed_user=author)
            serializer = SubscriptionSerializer(subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(Subscription, user=request.user, subscribed_user=author).delete()
        return Response({'detail': 'Вы успешно отписались'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт в/из избранного."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({'detail': 'Рецепт добавлен в избранное'}, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_200_OK)

        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response({'detail': 'Рецепт удалён из избранного'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт в/из корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({'detail': 'Рецепт добавлен в корзину'}, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в корзине'}, status=status.HTTP_200_OK)

        shopping_cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        shopping_cart.delete()
        return Response({'detail': 'Рецепт удалён из корзины'}, status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов с фильтрацией и поиском."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientSearchFilter
    pagination_class = None
    search_fields = ['^name']

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def search(self, request):
        """Поиск ингредиентов по части названия."""
        query = request.query_params.get('query', '')
        if query:
            ingredients = Ingredient.objects.filter(name__icontains=query)
            serializer = self.get_serializer(ingredients, many=True)
            return Response(serializer.data)
        return Response([], status=status.HTTP_400_BAD_REQUEST)


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
            queryset = queryset.filter(favorited_by__id=user.id)

        if self.request.query_params.get('is_in_shopping_cart') == '1' and user.is_authenticated:
            queryset = queryset.filter(in_shopping_cart__user=user)

        return queryset

    def add_ingredients(self, recipe, ingredients_data):
        """Добавление ингредиентов в рецепт."""
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, id=None):
        """Добавить/удалить рецепт в/из избранного."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({'detail': 'Рецепт добавлен в избранное'}, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_200_OK)

        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response({'detail': 'Рецепт удалён из избранного'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, id=None):
        """Добавить/удалить рецепт в/из корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            if created:
                return Response({'detail': 'Рецепт добавлен в корзину'}, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Рецепт уже в корзине'}, status=status.HTTP_200_OK)

        shopping_cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        shopping_cart.delete()
        return Response({'detail': 'Рецепт удалён из корзины'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).select_related('recipe')

        if not shopping_cart.exists():
            return Response({'detail': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)

        shopping_list = {}
        for item in shopping_cart:
            for ingredient in item.recipe.ingredients.all():
                name = ingredient.name
                amount = ingredient.amount
                measurement_unit = ingredient.measurement_unit
                if name in shopping_list:
                    shopping_list[name]['amount'] += amount
                else:
                    shopping_list[name] = {'amount': amount, 'measurement_unit': measurement_unit}

        shopping_text = "Список покупок:\n"
        for name, data in shopping_list.items():
            shopping_text += f"{name}: {data['amount']} {data['measurement_unit']}\n"

        response = HttpResponse(shopping_text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
