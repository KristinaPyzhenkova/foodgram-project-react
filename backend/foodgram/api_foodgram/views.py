from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .mixins import ListRetrieveViewSet
from .models import (
    User, Subscriber, Tag, Ingredient,
    Recipe, Amount, ShoppingCart, Favorite
)
from .filters import RecipeFilter, IngredientFilter
from .serializers import (
    TagSerializer, RecipeSerializer,
    RecipeSerializerGet, FavoriteRecipeSerializer,
    IngredientSerializerGet, UserSerializer,
    LiteRecipeSerializer,
    PasswordSerializer, NewUserSerializer,
    FavoriteSerializer, ShoppingCartSerializer,
    FollowListSerializer, FollowSerializer
)
from .pagination import FoodgramPagePagination


@permission_classes([permissions.AllowAny, ])
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Tag.
    Он позволяет получать данные о тэгах.
    """
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None


@permission_classes([permissions.IsAuthenticatedOrReadOnly, ])
class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Recipe.
    Он позволяет получать данные о рецептах, создавать, удалять и изменять их.
    Также добавлять рецепты в раздел "Избранное" или удалять их.
    Скачивать файл со списком покупок, добалять и удалять рецепты из него.
    Доступна фильтрация по избранному, автору, списку покупок и тегам.
    """
    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagePagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializerGet
        return RecipeSerializer

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def favorite(self, request, pk):
        current_user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe_in_favorite = Favorite.objects.filter(
            user=current_user, recipes=recipe
        )
        data = {'user': current_user.id, 'recipes': recipe.id}
        serializer = FavoriteSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            Favorite.objects.create(user=current_user, recipes=recipe)
            serializer = FavoriteRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe_in_favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        current_user = self.request.user
        recipe_in_shop = ShoppingCart.objects.filter(
            user=current_user, recipe=recipe
        )
        data = {'user': current_user.id, 'recipe': recipe.id}
        serializer = ShoppingCartSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'DELETE':
            recipe_in_shop.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        ShoppingCart.objects.create(user=current_user, recipe=recipe)
        serializer = LiteRecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, pk=None):
        ingredients = Amount.objects.filter(
            recipes__shopping__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_cart = ['Список покупок:\n--------------']
        for position, ingredient in enumerate(ingredients, start=1):
            shopping_cart.append(
                f'\n{position}. {ingredient["ingredients__name"]}:'
                f' {ingredient["amount"]}'
                f'({ingredient["ingredients__measurement_unit"]})'
            )
        response = HttpResponse(shopping_cart, content_type='text')
        return response


@permission_classes([permissions.AllowAny, ])
class IngredientViewSet(ListRetrieveViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Ingredient.
    Он позволяет получать данные обо всех ингредиентах
    или о каком-то определнном.
    """
    serializer_class = IngredientSerializerGet
    queryset = Ingredient.objects.all().order_by('name')
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


@permission_classes([permissions.AllowAny, ])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью User.
    Он позволяет получать данные о пользователях, о текущем пользователе(me),
    создавать пользователей и менять пароль, получать данные о подписках,
    подписываться и удалять подписки.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = FoodgramPagePagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return NewUserSerializer

    @action(
        detail=False,
        methods=['GET'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def change_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        author = self.request.user
        if serializer.is_valid(raise_exception=True):
            if not author.check_password(
                    serializer.data.get('current_password')
            ):
                return Response(
                    {'current_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            author.set_password(serializer.data.get('new_password'))
            author.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully'
            }
            return Response(response)

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, pk=None):
        subscriptions_list = self.paginate_queryset(
            User.objects.filter(subscribed__user=request.user)
        )
        serializer = FollowListSerializer(
            subscriptions_list, many=True, context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk):
        if request.method != 'POST':
            subscription = get_object_or_404(
                Subscriber,
                subscribed=get_object_or_404(User, id=pk),
                user=request.user
            )
            self.perform_destroy(subscription)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'subscribed': get_object_or_404(User, id=pk).id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
