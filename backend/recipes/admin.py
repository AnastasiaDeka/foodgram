"""Настройки админ-панели для приложения recipes."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов в рецептах."""

    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ("ingredient",)


class TagInline(admin.TabularInline):
    """Инлайн для тегов в рецепте."""

    model = Recipe.tags.through
    extra = 1
    min_num = 1


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для пользователей."""

    search_fields = ("email", "username")


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для рецептов."""

    list_display = ("name", "author")
    search_fields = ("name", "author__username")
    list_filter = ("tags",)
    inlines = [RecipeIngredientInline, TagInline]

    def get_favorites_count(self, obj):
        """Получение количества добавлений в избранное."""
        return obj.favorited_by.count()

    get_favorites_count.short_description = "В избранном"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов."""

    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов в рецепте."""

    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для избранных рецептов."""

    list_display = ("user", "recipe", "created_at")
    search_fields = ("user__username", "recipe__name")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для корзины покупок."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""

    list_display = ("user", "subscribed_user", "created_at")
    search_fields = ("user__username", "subscribed_user__username")
