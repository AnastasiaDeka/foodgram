import django_filters
from django_filters.rest_framework import FilterSet
from recipes.models import Recipe, Ingredient


class RecipeFilter(FilterSet):
    """Фильтр для рецептов с дополнительной оптимизацией."""

    author = django_filters.NumberFilter(field_name="author__id")
    is_favorited = django_filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = django_filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )
    tags = django_filters.AllValuesMultipleFilter(field_name="tags__slug")

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация избранных рецептов для авторизованных пользователей."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов в списке покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart=user)
        return queryset


class IngredientSearchFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов по названию."""

    name = django_filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ["name"]
