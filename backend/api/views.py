"""ViewSet модули для API."""

import os
from datetime import datetime

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription)
from users.models import User

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import PaginatorWithLimit
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (AvatarUpdateSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          SetPasswordSerializer, ShoppingCartRecipeSerializer,
                          SubscriptionSerializer, UserCreateSerializer,
                          UserProfileSerializer, UserSerializer,
                          UserUpdateSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
        """Получение прав для действий."""
        if self.action in ['handle_avatar', 'me', 'set_password']:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def handle_avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(
                user,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                old_avatar = user.avatar
                old_avatar_path = old_avatar.path if old_avatar else None

                serializer.save()

                if old_avatar_path and os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)

                return Response(
                    AvatarUpdateSerializer(
                        user, context={'request': request}
                    ).data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.avatar:
            avatar_path = user.avatar.path
            user.avatar = None
            user.save()

            if os.path.exists(avatar_path):
                os.remove(avatar_path)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение данных текущего пользователя."""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        """Изменение пароля пользователя."""
        serializer = SetPasswordSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            if not user.check_password(
                serializer.validated_data['current_password']
            ):
                return Response(
                    {'current_password': ['Неправильный пароль.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def register(self, request):
        """Регистрация нового пользователя."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        recipes_limit = int(request.query_params.get('recipes_limit', 3))

        queryset = (
            Subscription.objects.filter(user=request.user)
            .select_related('subscribed_user')
            .prefetch_related('subscribed_user__recipes')
            .order_by('-id')
        )

        page = self.paginate_queryset(queryset)

        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка и отписка от автора."""
        author = get_object_or_404(User, id=pk)

        if author == request.user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(
                user=request.user,
                subscribed_user=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=request.user,
                subscribed_user=author
            )
            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        get_object_or_404(
            Subscription,
            user=request.user,
            subscribed_user=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов с фильтрацией и поиском."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientSearchFilter
    pagination_class = None
    search_fields = ['^name']

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
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
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    pagination_class = PaginatorWithLimit
    serializer_class = RecipeSerializer

    def get_queryset(self):
        """Получение отфильтрованного списка рецептов."""
        queryset = super().get_queryset().order_by('-id')
        if self.request.user.is_authenticated:
            queryset = queryset.select_related('author')
        return queryset

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохранение рецепта с указанием автора."""
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        """Обновление рецепта с проверкой наличия tags."""
        if 'tags' not in request.data:
            return Response(
                {'tags': 'Поле tags обязательно для заполнения.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в/из корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        shopping_cart = get_object_or_404(
            ShoppingCart,
            user=user,
            recipe=recipe
        )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list = [
            f'Список покупок для пользователя {request.user.username}',
            f'Дата: {datetime.now().strftime("%d.%m.%Y")}',
            '',
        ]

        for i, item in enumerate(ingredients, 1):
            shopping_list.append(
                f'{i}. {item["ingredient__name"]} - '
                f'{item["total_amount"]} '
                f'{item["ingredient__measurement_unit"]}'
            )

        content = '\n'.join(shopping_list)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename=shopping_list.txt'
        )
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в/из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite = Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получение прямой короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)

        return Response({
            'short-link': f'{request.get_host()}/recipes/{recipe.pk}/'
        })
