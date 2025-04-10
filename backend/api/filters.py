"""Фильтры для API."""

import django_filters
from django_filters.rest_framework import FilterSet
from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтр для рецептов с поддержкой избранного и корзины покупок."""

    is_favorited = django_filters.CharFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart'
    )
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        """Метаданные фильтрации для модели Recipe."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация рецептов, добавленных в избранное."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов, находящихся в корзине покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset


class IngredientSearchFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов по названию."""

    name = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains'
    )

    class Meta:
        """Метаданные фильтрации для модели Ingredient."""

        model = Ingredient
        fields = ['name']
