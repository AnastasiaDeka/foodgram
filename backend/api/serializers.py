"""Сериализаторы для API."""

from django.contrib.auth import get_user_model
from drf_base64.fields import Base64ImageField
from django.contrib.auth.password_validation import validate_password
from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            Subscription, ShoppingCart, Favorite)
from rest_framework import serializers
from tags.models import Tag

User = get_user_model()




class UserCreateSerializer(serializers.ModelSerializer): 
    """Сериализатор для создания нового пользователя.""" 
 
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


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с количеством в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = RecipeIngredient
        fields = ['id', 'amount']

    def validate_id(self, value):
        """Проверка существования ингредиента с заданным id."""
        if not Ingredient.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(f'Ингредиент с id {value.id} не найден.')
        return value


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
    ingredients = IngredientAmountSerializer(many=True)
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

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        return data

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
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)

        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно при обновлении рецепта.'}
            )

        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)

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


class ShoppingCartRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в корзине."""

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def validate(self, data):
        """Валидируем, чтобы рецепт не был уже в корзине."""
        user = self.context["request"].user
        recipe = data["recipe"]

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в корзине.")
        return data

    def create(self, validated_data):
        """Сохраняем объект через сериализатор."""
        return ShoppingCart.objects.create(**validated_data)

    def to_representation(self, instance):
        """Преобразуем объект в нужный формат."""
        return {
            'user': instance.user.username,
            'recipe': instance.recipe.name,
            'recipe_id': instance.recipe.id,
        }


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def validate(self, data):
        """Валидируем, чтобы рецепт не был уже в избранном."""
        user = self.context["request"].user
        recipe = data["recipe"]

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в избранном.")
        return data

    def create(self, validated_data):
        """Сохраняем объект через сериализатор."""
        return Favorite.objects.create(**validated_data)

    def to_representation(self, instance):
        """Преобразуем объект в нужный формат."""
        return {
            'user': instance.user.username,
            'recipe': instance.recipe.name,
            'recipe_id': instance.recipe.id,
        }


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


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления информации о пользователе."""

    avatar = serializers.ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']
        extra_kwargs = {'email': {'required': True}}


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок, наследуется от UserSerializer."""

    id = serializers.IntegerField(source='subscribed_user.id')
    email = serializers.EmailField(source='subscribed_user.email')
    username = serializers.CharField(source='subscribed_user.username')
    first_name = serializers.CharField(source='subscribed_user.first_name')
    last_name = serializers.CharField(source='subscribed_user.last_name')
    avatar = serializers.ImageField(source='subscribed_user.avatar')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = list(UserSerializer.Meta.fields) + [
            'recipes',
            'recipes_count',
        ]

    def get_recipes(self, obj):
        """Получение рецептов автора с учетом лимита."""
        recipes_limit = self.context['request'].query_params.get('recipes_limit', 2)

        try:
            recipes_limit = int(recipes_limit)
        except ValueError:
            pass

        recipes = obj.subscribed_user.recipes.all()[:recipes_limit]

        return ShoppingCartRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.subscribed_user.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_user')

    def validate(self, data):
        """Проверяем, что нельзя подписаться на самого себя и нельзя дублировать подписку."""
        request = self.context.get('request')
        user = request.user
        subscribed_user = data.get('subscribed_user')

        if user == subscribed_user:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'}
            )

        if Subscription.objects.filter(user=user, subscribed_user=subscribed_user).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны.'}
            )

        return data

    def create(self, validated_data):
        """Создаём объект подписки."""
        return Subscription.objects.create(**validated_data)


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Мета-класс для настройки сериализатора."""

        model = User
        fields = ['avatar']

    def validate(self, data):
        """Глобальная валидация данных."""
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'avatar': 'Поле avatar обязательно для загрузки.'}
            )
        return data
