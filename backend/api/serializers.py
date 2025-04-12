"""Сериализаторы для API."""

from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user, subscribed_user=obj
            ).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с количеством в рецепте."""

    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    id = serializers.ReadOnlyField(source='ingredient.id')

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов при создании/обновлении рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(many=True,
                                             source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'name',
            'text',
            'cooking_time',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'ingredients',
        )

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.favorited_by.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в корзине."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.in_shopping_cart.filter(user=request.user).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountCreateUpdateSerializer(many=True)
    author = UserSerializer(read_only=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'image',
            'tags',
            'ingredients',
            'cooking_time',
            'author',
        )

    def validate(self, data):
        """Общая валидация полей."""
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо выбрать хотя бы один тег.'}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент для рецепта.'}
            )

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        return data

    def create(self, validated_data):
        """Создание нового рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance = super().update(instance, validated_data)

        instance.tags.clear()
        instance.tags.set(tags)

        instance.ingredients.clear()
        self._set_ingredients(instance, ingredients)

        return instance

    @staticmethod
    def _set_ingredients(recipe, ingredients):
        """Вспомогательный метод для обновления ингредиентов."""
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ])

    def to_representation(self, instance):
        """Преобразование объекта в JSON."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детализированного представления рецепта."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = ShoppingCart
        fields = ['user', 'recipe']

    def validate(self, data):
        """Валидируем, чтобы рецепт не был уже в корзине."""
        user = self.context["request"].user
        recipe = data["recipe"]

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в корзине.")
        return data

    def to_representation(self, instance):
        """Преобразуем объект в нужный формат."""
        return RecipeDetailSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Валидируем, чтобы рецепт не был уже в избранном."""
        user = self.context["request"].user
        recipe = data["recipe"]

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в избранном.")
        return data

    def to_representation(self, instance):
        """Преобразуем объект в нужный формат."""
        return RecipeDetailSerializer(
            instance.recipe, context=self.context
        ).data


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    avatar = serializers.ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar')

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя."""
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для отображения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        """Мета-класс для настройки сериализатора."""

        fields = (
            *UserSerializer.Meta.fields,
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Получает ограниченный список рецептов подписанного пользователя."""
        request = self.context.get('request')
        recipes_limit = (
            request.query_params.get('recipes_limit')
            if request else None
        )
        recipes = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return RecipeDetailSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    subscribed_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Subscription
        fields = ('user', 'subscribed_user')

    def validate(self, data):
        """
        Проверяет, что нельзя подписаться на самого себя.

        или подписаться дважды.
        """
        request = self.context.get('request')
        user = request.user
        subscribed_user = data.get('subscribed_user')

        if user == subscribed_user:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'}
            )

        if Subscription.objects.filter(
            user=user, subscribed_user=subscribed_user
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя.'}
            )

        return data

    def to_representation(self, instance):
        """Возвращает данные о подписанном пользователе."""
        return SubscriptionSerializer(
            instance.subscribed_user, context=self.context
        ).data


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = ('avatar',)

    def validate(self, data):
        """Глобальная валидация данных."""
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'avatar': 'Поле avatar обязательно для загрузки.'}
            )
        return data
