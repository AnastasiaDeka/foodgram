from drf_base64.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Subscription
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


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'ingredients', 'cooking_time')

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError('Рецепт должен содержать хотя бы один ингредиент.')
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('Время приготовления должно быть положительным.')
        return value



class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), many=True)

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


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email и пароль обязательны.')
        
        # Получаем пользователя с заданным email
        user = User.objects.filter(email=email).first()

        # Если пользователь не найден
        if user is None:
            raise serializers.ValidationError('Неверные учетные данные.')

        # Если пароль неверный
        if not user.check_password(password):
            raise serializers.ValidationError('Неверные учетные данные.')

        # Если пользователь не активен
        if not user.is_active:
            raise serializers.ValidationError('Аккаунт не активирован.')

        data['user'] = user
        return data


class SubscriptionMixin:
    def get_subscription_status(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(user=user, author=obj).exists()


class UserProfileSerializer(SubscriptionMixin, serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')


class UserChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not authenticate(username=user.email, password=value):
            raise serializers.ValidationError('Текущий пароль неверен.')
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self, validated_data):
        user = self.context['request'].user
        user.password = make_password(validated_data['new_password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе."""
    avatar = Base64ImageField(use_url=True, required=False)  # Добавлено поле для аватара
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'is_subscribed']  # Учитываем аватар
        read_only_fields = ['id']
    
    def get_is_subscribed(self, obj):

        return obj.subscriptions.exists()

    def to_representation(self, instance):
        # Отладочный вывод для проверки данных
        print(f"Serializing user: {instance.username}")  # Вывод имени пользователя для отладки
        print(f"All users: {[user.username for user in User.objects.all()]}")  # Вывод всех пользователей
        
        return super().to_representation(instance)


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""
    #avatar = Base64ImageField(use_url=True, required=False)  # Добавлено поле для аватара

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']  # Учитываем аватар
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
    avatar = Base64ImageField(use_url=True, required=False)  # Добавлено поле для аватара

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']  # Учитываем аватар
        extra_kwargs = {
            'email': {'required': True}
        }


class SetPasswordSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля пользователя.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Логика валидации пароля
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if old_password == new_password:
            raise serializers.ValidationError("Новый пароль не может быть таким же, как старый.")

        return data

    def set_password(self, user):
        """
        Метод для изменения пароля пользователя.
        """
        user.set_password(self.validated_data['new_password'])
        user.save()


class SubscriptionSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email')
    author_username = serializers.CharField(source='author.username')

    class Meta:
        model = Subscription
        fields = ('author_email', 'author_username', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscription.objects.filter(user=user, author=obj.author).exists()
