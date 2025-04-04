"""ViewSet модули для API."""

import os
from datetime import datetime

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription)
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import User
from tags.models import Tag

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import PaginatorWithLimit
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (AvatarUpdateSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          FavoriteSerializer, ShoppingCartSerializer,
                          SubscriptionCreateSerializer,
                          SubscriptionSerializer,
                          UserProfileSerializer, UserSerializer,
                          UserUpdateSerializer, TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None

class UserViewSet(DjoserUserViewSet):
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
        return UserUpdateSerializer


    @action(detail=False, methods=['put'])
    def update_avatar(self, request):
        """Обновление аватара пользователя."""
        user = request.user
        serializer = AvatarUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            AvatarUpdateSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение данных текущего пользователя."""
        super().retrieve(request)

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
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка на автора."""
        author = get_object_or_404(User, id=pk)
        serializer = SubscriptionCreateSerializer(
            data={'subscribed_user': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save(user=request.user)

        return Response(
            SubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписка от автора."""
        author = get_object_or_404(User, id=pk)

        subscription = Subscription.objects.filter(
            user=request.user,
            subscribed_user=author
        ).first()

        if not subscription:
            return Response(
                {'error': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов с фильтрацией и поиском."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientSearchFilter
    pagination_class = None
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами с фильтрацией."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    pagination_class = PaginatorWithLimit
    serializer_class = RecipeSerializer

    def get_queryset(self):
        """Получение отфильтрованного списка рецептов с учетом лимита."""
        queryset = super().get_queryset().order_by('-id')


        max_limit = 200

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit > max_limit:
                    recipes_limit = max_limit
                queryset = queryset[:recipes_limit]
            except ValueError:
                raise ValidationError(
                    "Invalid value for 'recipes_limit'. It must be an integer."
                )

        if self.request.user.is_authenticated:
            queryset = queryset.select_related('author')

        return queryset

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def add_to_shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        serializer = ShoppingCartSerializer(data={'user': user.id, 'recipe': recipe.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe).first()

        if not shopping_cart:
            return Response(
                {'error': 'Рецепта нет в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
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
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def add_to_favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        serializer = FavoriteSerializer(data={'user': user.id, 'recipe': recipe.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        favorite = Favorite.objects.filter(user=request.user, recipe_id=pk).first()

        if not favorite:
            return Response(
                {'error': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
