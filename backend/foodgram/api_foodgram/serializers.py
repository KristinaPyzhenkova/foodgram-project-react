from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from .models import (
    User, Subscriber, Tag, Ingredient,
    Recipe, Amount, RecipeTag,
    Favorites, ShoppingCart
)


class NewUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новых пользователей.
    """

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name')


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователей.
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, following):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscriber.objects.filter(
            user=request.user, subscribed=following
        ).exists()


class PasswordSerializer(serializers.ModelSerializer):
    """
    Сериализатор для изменения пароля.
    """

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('new_password', 'current_password')


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения игредиентов.
    """

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class AmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения кол-ва игредиентов.
    """
    ingredients = IngredientSerializer()

    class Meta:
        fields = ('ingredients', 'amount')
        model = Amount


class RecipeSerializerGet(serializers.ModelSerializer):
    """
    Сериализатор для получения рецепта.
    """
    ingredients = AmountSerializer(
        source='amount',
        many=True,
        read_only=True
    )
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        fields = (
            'id', 'tags', 'author', 'image', 'name', 'text',
            'cooking_time', 'ingredients', 'is_favorite', 'is_in_shopping_cart'
        )
        model = Recipe

    def get_is_favorite(self, recipes):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorites.objects.filter(
            user=request.user, recipes=recipes
        ).exists()

    def get_is_in_shopping_cart(self, recipes):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorites.objects.filter(
            user=request.user, recipes=recipes
        ).exists()


class AmountForCreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор кол-во игредиетов для создания рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        fields = ('id', 'amount')
        model = Amount


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.
    """
    ingredients = AmountForCreateRecipeSerializer(
        source='amount',
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'author',
            'image', 'name', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('amount')
        tags = validated_data.pop('tags')
        recipes = Recipe.objects.create(**validated_data)
        Amount.objects.bulk_create(
            [Amount(
                amount=ingredient['amount'],
                recipes=recipes,
                ingredients=ingredient['id']
            ) for ingredient in ingredients]
        )
        RecipeTag.objects.bulk_create(
            [RecipeTag(
                tags=tag,
                recipes=recipes
            ) for tag in tags]
        )
        return recipes

    def update(self, instance, validated_data):
        Amount.objects.filter(recipes=instance.id).all().delete()
        RecipeTag.objects.filter(recipes=instance.id).all().delete()
        tags = validated_data.get('tags')
        ingredients = validated_data.get('amount')
        Amount.objects.bulk_create(
            [Amount(
                amount=ingredient['amount'],
                recipes=instance,
                ingredients=ingredient['id']
            ) for ingredient in ingredients]
        )
        RecipeTag.objects.bulk_create(
            [RecipeTag(
                tags=tag,
                recipes=instance
            ) for tag in tags]
        )
        instance.save()
        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для избранного.
    """
    image = Base64ImageField(required=False)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        favorite = Favorites.objects.filter(user=user, recipes=recipe)
        if self.context.get('request').method == 'POST':
            if favorite.exists():
                raise serializers.ValidationError({
                    'errors': 'Такая подписка уже оформлена!'
                })
        if not favorite.exists():
            raise serializers.ValidationError({
                'errors': 'Такой подписки не существует!'
            })
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для избранного.
    """

    class Meta:
        fields = ('recipes', 'user')
        model = Favorites

    def validate(self, data):
        user = data['user']
        recipe = data['recipes']
        favorite = Favorites.objects.filter(user=user, recipes=recipe)
        if self.context.get('request').method == 'POST':
            if favorite.exists():
                raise serializers.ValidationError({
                    'errors': 'Данный рецепт добавлен в избранное!'
                })
            return data
        if self.context.get('request').method == 'DELETE':
            if not favorite.exists():
                raise serializers.ValidationError({
                    'errors': 'Данного рецепта в избранном не существует!'
                })
            return data


class IngredientSerializerGet(serializers.ModelSerializer):
    """
    Сериализатор для получения игредиентов.
    """

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class LiteRecipeSerializer(serializers.ModelSerializer):
    """
    Сокращенный сериализатор рецепта.
    """
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка покупок.
    """

    class Meta:
        fields = ('recipe', 'user')
        model = ShoppingCart

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        shopping_list = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if self.context.get('request').method == 'POST':
            if shopping_list.exists():
                raise serializers.ValidationError({
                    'errors': 'Данный рецепт добавлен уже в список покупок!'
                })
            return data
        if self.context.get('request').method == 'DELETE':
            if not shopping_list.exists():
                raise serializers.ValidationError({
                    'errors': 'Данного рецепта нет в списке покупок!'
                })
            return data


class SubscriptionUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок.
    """
    recipes = LiteRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, following):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscriber.objects.filter(
            user=request.user, subscribed=following
        ).exists()


class SubscriberSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок.
    """

    class Meta:
        fields = ('subscribed', 'user')
        model = Subscriber

    def validate(self, data):
        user = data['user']
        subscribed = data['subscribed']
        subscribed_user = Subscriber.objects.filter(
            user=user, subscribed=subscribed
        )
        if self.context.get('request').method == 'POST':
            if subscribed_user.exists():
                raise serializers.ValidationError({
                    'errors': 'На данного пользователя уже подписка!'
                })
            return data
        if self.context.get('request').method == 'DELETE':
            if not subscribed_user.exists():
                raise serializers.ValidationError({
                    'errors': 'На данного пользователя нет подписки!'
                })
            return data
