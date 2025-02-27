"""Модели для приложения рецептов."""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User
from tags.models import Tag


class Ingredient(models.Model):
    """Модель ингредиента."""

    MEASUREMENT_UNITS = [
        ('шт', 'Штуки'),
        ('г', 'Граммы'),
        ('мл', 'Миллилитры'),
    ]

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=50,
        choices=MEASUREMENT_UNITS,
        default='шт',
        verbose_name='Единица измерения'
    )

    class Meta:
        """Мета-класс для настройки порядка и отображения ингредиентов."""

        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes_images/',
        verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (мин)'
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )

    class Meta:
        """Мета-класс для настройки порядка и отображения рецептов."""

        ordering = ['-published_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает строковое представление рецепта."""
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта с ингредиентами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )

    class Meta:
        """Мета-класс для настройки ингредиентов в рецепте."""

        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        """Возвращает строковое представление ингредиента в рецепте."""
        return (
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'{self.ingredient.name}'
        )


class Favorite(models.Model):
    """Модель избранного рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        """Мета-класс для настройки избранных рецептов."""

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        """Возвращает строковое представление избранного рецепта."""
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        """Мета-класс для настройки списка покупок."""

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        """Возвращает строковое представление рецепта в списке покупок."""
        return f'{self.user} добавил {self.recipe} в список покупок'


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    subscribed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='На кого подписан'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        """Мета-класс для настройки уникальности и отображения подписок."""

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_user'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f'{self.user} подписан на {self.subscribed_user}'
