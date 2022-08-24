from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from .models import (Users, Subscribed, Tags, Ingredients,
                     Recipes, Amount, RecipesTags, Favorites)


class NewUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новых пользователей.
    """

    class Meta:
        model = Users
        fields = ('email', 'id', 'username', 'first_name', 'last_name')


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователей.
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, following):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribed.objects.filter(
            user=request.user, subscribed=following
        ).exists()


class PasswordSerializer(serializers.ModelSerializer):
    """
    Сериализатор для изменения пароля.
    """

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = Users
        fields = ('new_password', 'current_password')


class TagsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        fields = '__all__'
        model = Tags


class IngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения игредиентов.
    """

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredients


class AmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения кол-ва игредиентов.
    """
    ingredients = IngredientsSerializer()

    class Meta:
        fields = ('ingredients', 'amount')
        model = Amount


class RecipesSerializerGet(serializers.ModelSerializer):
    """
    Сериализатор для получения рецепта.
    """
    ingredients = AmountSerializer(
        source='amount_r',
        many=True,
        read_only=True
    )
    tags = TagsSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        fields = (
            'id', 'tags', 'author', 'image', 'name', 'text',
            'cooking_time', 'ingredients', 'is_favorite', 'is_in_shopping_cart'
        )
        model = Recipes

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


class AmountSerializerP(serializers.ModelSerializer):
    """
    Сериализатор кол-во игредиетов для создания рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )

    class Meta:
        fields = ('id', 'amount')
        model = Amount


class RecipesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.
    """
    ingredients = AmountSerializerP(
        source='amount_r',
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipes
        fields = (
            'ingredients', 'tags', 'author',
            'image', 'name', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('amount_r')
        tags = validated_data.pop('tags')
        recipes = Recipes.objects.create(**validated_data)
        for ingredient in ingredients:
            ingr = Ingredients.objects.get(id=ingredient['id'].id)
            Amount.objects.create(
                amount=ingredient['amount'], recipes=recipes, ingredients=ingr
            )
        for tag in tags:
            RecipesTags.objects.create(tags=tag, recipes=recipes)
        return recipes

    def update(self, instance, validated_data):
        Amount.objects.filter(recipes=instance.id).all().delete()
        RecipesTags.objects.filter(recipes=instance.id).all().delete()
        tags = validated_data.get('tags')
        ingredients = validated_data.get('amount_r')
        for ingredient in ingredients:
            ingr = Ingredients.objects.get(id=ingredient['id'].id)
            Amount.objects.create(
                amount=ingredient['amount'], recipes=instance, ingredients=ingr
            )
        for tag in tags:
            RecipesTags.objects.create(tags=tag, recipes=instance)
        instance.save()
        return instance


class FavoriteRecipesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для избранного.
    """
    image = Base64ImageField(required=False)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipes


class IngredientsSerializerGet(serializers.ModelSerializer):
    """
    Сериализатор для получения игредиентов.
    """

    class Meta:
        fields = '__all__'
        model = Ingredients


class LiteRecipeSerializer(serializers.ModelSerializer):
    """
    Сокращенный сериализатор рецепта.
    """
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок.
    """
    recipe = LiteRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'recipe', 'recipes_count', 'is_subscribed'
        )

    def get_recipes_count(self, obj):
        return (obj.recipe.count())

    def get_is_subscribed(self, following):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribed.objects.filter(
            user=request.user, subscribed=following
        ).exists()
