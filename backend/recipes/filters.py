"""Модуль фильтров для рецептов."""

import django_filters
from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    tags = django_filters.CharFilter(
        field_name='tags__slug',
        method='filter_tags'
    )
    author = django_filters.NumberFilter(
        field_name='author__id'
    )
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        """Мета-класс для фильтрации рецептов."""

        model = Recipe
        fields = ['tags', 'author']

    def filter_tags(self, queryset, name, value):
        """Фильтрация по слагу тега."""
        return queryset.filter(tags__slug=value)

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранным рецептам."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по корзине покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
