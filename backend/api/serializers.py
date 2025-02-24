from drf_base64.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Subscription, RecipeIngredient
from tags.models import Tag
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from tags.models import Tag
from recipes.models import Ingredient, Recipe, Subscription
from django.core.exceptions import ValidationError
User = get_user_model()
ERROR_MESSAGE = 'Не удается войти с предоставленными учетными данными.'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit'] 


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'ingredients', 'cooking_time')

    def validate_ingredients(self, value):
        """Проверка, что в рецепте есть хотя бы один ингредиент."""
        if len(value) == 0:
            raise serializers.ValidationError('Рецепт должен содержать хотя бы один ингредиент.')
        return value

    def validate_cooking_time(self, value):
        """Проверка, что время приготовления положительное."""
        if value <= 0:
            raise serializers.ValidationError('Время приготовления должно быть положительным.')
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientWithAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с указанием количества в рецепте."""
    id = serializers.IntegerField()
    name = serializers.CharField(source='ingredient.name', read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount']
    

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientWithAmountSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'ingredients', 'cooking_time')

    def validate_ingredients(self, value):
        """Проверка, что в рецепте есть хотя бы один ингредиент."""
        if len(value) == 0:
            raise serializers.ValidationError('Рецепт должен содержать хотя бы один ингредиент.')
        return value

    def validate_cooking_time(self, value):
        """Проверка, что время приготовления положительное."""
        if value <= 0:
            raise serializers.ValidationError('Время приготовления должно быть положительным.')
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])

            amount = ingredient_data['amount']

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )

        return recipe


class SubscriptionMixin:
    """Миксин для получения статуса подписки пользователя."""
    def get_subscription_status(self, obj):
        """Проверяет, подписан ли текущий пользователь на переданного пользователя."""
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(user=user, subscribed_user=obj).exists()


class UserProfileSerializer(SubscriptionMixin, serializers.ModelSerializer):
    """Сериализатор для профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Определяет, подписан ли текущий пользователь на этого пользователя."""
        return self.get_subscription_status(obj)


class UserChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate_current_password(self, value):
        """Проверка текущего пароля пользователя."""
        user = self.context['request'].user
        if not authenticate(username=user.email, password=value):
            raise serializers.ValidationError('Текущий пароль неверен.')
        return value

    def validate_new_password(self, value):
        """Проверка нового пароля пользователя с использованием стандартных валидаторов."""
        validate_password(value)
        return value

    def save(self, validated_data):
        """Сохраняет новый пароль пользователя в базе данных."""
        user = self.context['request'].user
        user.password = make_password(validated_data['new_password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""
    id = serializers.IntegerField(read_only=True)
    avatar = serializers.ImageField(use_url=True, required=False)
    is_subscribed = serializers.SerializerMethodField()
    

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'is_subscribed']
        read_only_fields = ['id']
    
    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на этого пользователя."""
        return obj.subscriptions.exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""
    avatar = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, password):
        """Проверка пароля пользователя с использованием стандартных валидаторов."""
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
    avatar = Base64ImageField(use_url=True, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']
        extra_kwargs = {
            'email': {'required': True}
        }


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Проверка, что новый пароль не совпадает с текущим."""
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if current_password == new_password:
            raise serializers.ValidationError("Новый пароль не может быть таким же, как старый.")

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
            raise ValueError("User must be provided to save the password.")


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок."""
    id = serializers.IntegerField(source='subscribed_user.id')
    author_email = serializers.EmailField(source='subscribed_user.email')
    author_username = serializers.CharField(source='subscribed_user.username')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('id', 'author_email', 'author_username', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, subscribed_user=obj.subscribed_user).exists()
