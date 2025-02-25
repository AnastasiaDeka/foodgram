from drf_base64.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Subscription, RecipeIngredient, ShoppingCart
from tags.models import Tag
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from tags.models import Tag
from django.core.exceptions import ValidationError

User = get_user_model()
ERROR_MESSAGE = 'Не удается войти с предоставленными учетными данными.'


from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users.models import User


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с количеством в рецепте."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']

    def to_representation(self, instance):
        """Форматируем ответ с полной информацией об ингредиенте."""
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }



class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = '__all__'


class UserReadSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для чтения (GET)."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.subscriptions.filter(subscribed_user=obj).exists())


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра рецепта."""
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField(use_url=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(many=True, source='recipe_ingredients')

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'ingredients', 'cooking_time', 'author')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountSerializer(many=True)
    author = UserReadSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'ingredients', 'cooking_time', 'author')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        user = self.context['request'].user

        # Удаляем author из validated_data, так как мы присваиваем его вручную
        validated_data.pop('author', None)

        # Создаем рецепт
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)

        # Обрабатываем ингредиенты
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe



class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов (с дополнительной информацией)."""
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField(use_url=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'is_favorited', 
                  'is_in_shopping_cart', 'cooking_time', 'author')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated and
            Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated and
            ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""
    recipe = RecipeSerializer()  # Сериализатор для рецепта
    ingredients = serializers.SerializerMethodField()  # Список ингредиентов

    class Meta:
        model = ShoppingCart
        fields = ['recipe', 'ingredients']

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов для рецепта в корзине."""
        return [
            {
                'ingredient': recipe_ingredient.ingredient.name,
                'amount': recipe_ingredient.amount,
                'measurement_unit': recipe_ingredient.ingredient.measurement_unit,
            }
            for recipe_ingredient in obj.recipe.recipe_ingredients.all()
        ]

class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'recipe',
            'user'
        )

    def validate(self, data):
        user = data['user']
        recipe_id = data['recipe'].id
        if ShoppingCart.objects.filter(
            user=user,
            recipe__id=recipe_id
        ).exists():
            raise ValidationError(SHOPLIST_ADDED)
        return data

class SubscriptionMixin:
    """Миксин для получения статуса подписки пользователя."""
    def get_subscription_status(self, obj):
        """Проверяет, подписан ли текущий пользователь на переданного пользователя."""
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(user=user, subscribed_user=obj).exists()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar']

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя, если он есть."""
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


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
    is_subscribed = serializers.SerializerMethodField()
    

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'is_subscribed']
        read_only_fields = ['id']
    
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, subscribed_user=obj).exists()



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
    avatar = serializers.ImageField(required=True)

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


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar']

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя, если он есть."""
        request = self.context.get('request')
        if obj.avatar and request:

            return request.build_absolute_uri(obj.avatar.url)
        return None
