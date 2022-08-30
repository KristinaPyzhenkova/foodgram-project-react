from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.generics import get_object_or_404

from .models import (
    User, Subscriber, Tag, Ingredient,
    Recipe, Amount,
    Favorite, ShoppingCart
)


class NewUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новых пользователей.
    """

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


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
    color = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag

    def get_color(self, obj):
        return f'{obj.color}'


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


class AmountIngredientForRecipeGetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit', read_only=True
    )
    id = serializers.IntegerField(source='ingredient.id', read_only=True)

    class Meta:
        model = Amount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AmountForCreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор кол-во игредиетов для создания рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = Amount
        fields = ('id', 'amount')


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
        favorite = Favorite.objects.filter(user=user, recipes=recipe)
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
        model = Favorite

    def validate(self, data):
        user = data['user']
        recipe = data['recipes']
        favorite = Favorite.objects.filter(user=user, recipes=recipe)
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


class FollowListSerializer(serializers.ModelSerializer):
    """ Сериализация списка на кого подписан пользователь"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes_count(self, following):
        return Recipe.objects.filter(author=following).count()

    def get_recipes(self, following):
        queryset = self.context.get('request')
        recipes_limit = queryset.query_params.get('recipes_limit')
        if not recipes_limit:
            return RecipeFollowingSerializer(
                following.recipes.all(),
                many=True, context={'request': queryset}
            ).data
        return RecipeFollowingSerializer(
            following.recipes.all()[:int(recipes_limit)], many=True,
            context={'request': queryset}
        ).data

    def get_is_subscribed(self, following):
        return Subscriber.objects.filter(
            user=self.context.get('request').user,
            subscribed=following
        ).exists()


class RecipeFollowingSerializer(serializers.ModelSerializer):
    """ Сериализация списка рецептов на кого подписан пользователь """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализация при подписке на пользователя """

    class Meta:
        model = Subscriber
        fields = ('user', 'subscribed')

    def validate(self, data):
        get_object_or_404(User, username=data['subscribed'])
        if self.context['request'].user == data['subscribed']:
            raise serializers.ValidationError('Сам на себя подписываешься!')
        if Subscriber.objects.filter(
                user=self.context['request'].user,
                subscribed=data['subscribed']
        ):
            raise serializers.ValidationError('Уже подписан')
        return data

    def to_representation(self, instance):
        return FollowListSerializer(
            instance.subscribed,
            context={'request': self.context.get('request')}
        ).data


class IngredientRecipeSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(source="ingredients.id")
    name = serializers.ReadOnlyField(source="ingredients.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredients.measurement_unit"
    )

    class Meta:
        model = Amount
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializerGet(serializers.ModelSerializer):
    """
    Сериализатор для получения рецепта.
    """
    ingredients = IngredientRecipeSerializer(
        many=True, source="amount"
    )
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        fields = (
            'id', 'tags', 'author', 'image', 'name', 'text',
            'cooking_time', 'ingredients', 'is_favorited',
            'is_in_shopping_cart'
        )
        model = Recipe

    def get_is_favorited(self, recipes):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipes=recipes
        ).exists()

    def get_is_in_shopping_cart(self, recipes):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=recipes
        ).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True, source="amount"
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    @staticmethod
    def parse_ingredients(recipe, data):
        for ingredient_data in data:
            try:
                ingredient_current = Ingredient.objects.get(
                    pk=ingredient_data["ingredients"]["id"]
                )
            except serializers.ValidationError:
                raise serializers.ValidationError("Miss ingredient")
            Amount.objects.create(
                recipes=recipe,
                amount=ingredient_data["amount"],
                ingredients=ingredient_current,
            )

    def create(self, validated_data):
        if "tags" in validated_data:
            tags = validated_data.pop("tags")
        ingredients_data = validated_data.pop("amount")
        recipe = super().create(validated_data)
        recipe.tags.add(*tags)
        self.parse_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if "tags" in validated_data:
            tags = validated_data.pop("tags")
            instance.tags.clear()
            instance.tags.add(*tags)
        ingredients_data = validated_data.pop("amount")
        Amount.objects.filter(recipes=instance).delete()
        self.parse_ingredients(instance, ingredients_data)
        validated_data['author'] = instance.author
        print(validated_data)
        recipe = super().update(instance, validated_data)
        return recipe

    def validate(self, data):
        ingredients = []
        for ingredient in data['amount']:
            if ingredient['ingredients']['id'] not in ingredients:
                ingredients.append(ingredient['ingredients']['id'])
            else:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!')
        tags = []
        for tag in data["tags"]:
            if tag not in tags:
                tags.append(tag)
            else:
                raise serializers.ValidationError(
                    "Тэги не должны повторяться!"
                )
        return data
