"""Сериализаторы для API."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription)
from rest_framework import serializers
from tags.models import Tag

User = get_user_model()
ERROR_MESSAGE = 'Не удается войти с предоставленными учетными данными.'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с количеством в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = RecipeIngredient
        fields = ['id', 'amount']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Tag
        fields = '__all__'


class UserReadSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для чтения (GET)."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(
                subscribed_user=obj
            ).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserReadSerializer(read_only=True)

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

    def get_tags(self, obj):
        """Получает список тегов рецепта."""
        return [
            {'id': tag.id, 'name': tag.name, 'slug': tag.slug}
            for tag in obj.tags.all()
        ]

    def get_ingredients(self, obj):
        """Получает список ингредиентов рецепта."""
        recipe_ingredients = obj.recipe_ingredients.all()
        return [
            {
                'id': ri.ingredient.id,
                'amount': float(ri.amount),
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
            }
            for ri in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в корзине."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)
    author = UserReadSerializer(read_only=True)

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

    def validate_ingredients(self, value):
        """Проверка ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент для рецепта.'
            )

        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return value

    def create(self, validated_data):
        """Создание нового рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients)

        return instance

    def _create_ingredients(self, recipe, ingredients):
        """Вспомогательный метод для создания ингредиентов."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        """Преобразование объекта в JSON."""
        return RecipeSerializer(instance, context=self.context).data


class SubscriptionMixin:
    """Миксин для получения статуса подписки пользователя."""

    def get_subscription_status(self, obj):
        """Проверка подписки текущего пользователя."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Subscription.objects.filter(
                user=user, subscribed_user=obj
            ).exists()
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    avatar = serializers.ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar']

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя."""
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        ]
        read_only_fields = ['id']

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, subscribed_user=obj
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""

    avatar = serializers.ImageField(use_url=True, required=False)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'avatar',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, password):
        """Проверка пароля пользователя."""
        validate_password(password)
        return password

    def create(self, validated_data):
        """Создание нового пользователя с заданными данными."""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления информации о пользователе."""

    avatar = serializers.ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']
        extra_kwargs = {'email': {'required': True}}


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""

    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Проверка, что новый пароль не совпадает с текущим."""
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if current_password == new_password:
            raise serializers.ValidationError(
                'Новый пароль не может быть таким же, как старый.'
            )

        return data

    def set_password(self, user):
        """Изменение пароля пользователя."""
        user.set_password(self.validated_data['new_password'])
        user.save()

    def save(self, user=None):
        """Сохранение нового пароля пользователя."""
        if user is not None:
            self.set_password(user)
        else:
            raise ValueError('User must be provided to save the password.')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    id = serializers.IntegerField(source='subscribed_user.id')
    email = serializers.EmailField(source='subscribed_user.email')
    username = serializers.CharField(source='subscribed_user.username')
    first_name = serializers.CharField(source='subscribed_user.first_name')
    last_name = serializers.CharField(source='subscribed_user.last_name')
    avatar = serializers.ImageField(source='subscribed_user.avatar')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Subscription
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Subscription.objects.filter(
                user=user, subscribed_user=obj.subscribed_user
            ).exists()
        )

    def get_recipes(self, obj):
        """Получение рецептов автора с учетом лимита."""
        recipes_limit = self.context.get('recipes_limit')
        recipes = obj.subscribed_user.recipes.all()[:recipes_limit]
        return RecipeSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.subscribed_user.recipes.count()


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = ['avatar']

    def validate_avatar(self, value):
        """Валидация аватара."""
        if not value:
            raise serializers.ValidationError(
                'Необходимо загрузить изображение.'
            )

        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                'Размер изображения не должен превышать 50MB.'
            )

        allowed_formats = ['image/jpeg', 'image/jpg', 'image/png']
        if (hasattr(value, 'content_type')
                and value.content_type not in allowed_formats):
            raise serializers.ValidationError(
                'Поддерживаются только форматы JPEG и PNG.'
            )

        return value

    def update(self, instance, validated_data):
        """Обновление аватара пользователя."""
        if 'avatar' in validated_data:
            if instance.avatar:
                instance.avatar.delete(save=False)

            instance.avatar = validated_data['avatar']
            instance.save()

        return instance
