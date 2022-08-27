from datetime import datetime, timedelta

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import jwt
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework.authtoken import views as auth_views
from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas import ManualSchema

from .mixins import ListRetrieveViewSet
from .models import (
    User, Subscriber, Tag, Ingredient,
    Recipe, Amount, ShoppingCart, Favorite
)
from .filters import RecipeFilter
from .serializers import (
    TagSerializer, RecipeSerializer,
    RecipeSerializerGet, FavoriteRecipeSerializer,
    IngredientSerializerGet, UserSerializer,
    LiteRecipeSerializer, SubscriptionUserSerializer,
    PasswordSerializer, NewUserSerializer,
    FavoriteSerializer, ShoppingCartSerializer,
    SubscriberSerializer, MyAuthTokenSerializer
)
from .pagination import UserPagination
from .utils import get_ingredients_list_for_shopping


@permission_classes([permissions.AllowAny, ])
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Tag.
    Он позволяет получать данные о тэгах.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


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
    serializer_class = RecipeSerializer
    pagination_class = UserPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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
    def download_shopping_cart(self, request):
        ingredients = Amount.objects.filter(
            recipes__shopping__user=request.user).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(Sum('amount'))
        main_list = get_ingredients_list_for_shopping(ingredients)
        response = HttpResponse(main_list, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="Cart.txt"'
        return response


@permission_classes([permissions.AllowAny, ])
class IngredientViewSet(ListRetrieveViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Ingredient.
    Он позволяет получать данные обо всех ингредиентах
    или о каком-то определнном.
    """
    serializer_class = IngredientSerializerGet
    queryset = Ingredient.objects.all()
    pagination_class = UserPagination


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
    pagination_class = UserPagination

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
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(subscribed__user=request.user)
        serializer = SubscriptionUserSerializer(
            subscriptions,
            context=self.get_serializer_context(),
            many=True
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions_create_delete(self, request, pk):
        subscribed = get_object_or_404(User, pk=pk)
        current_user = self.request.user
        subscribed_in = Subscriber.objects.filter(
            user=current_user, subscribed=subscribed
        )
        data = {'user': current_user.id, 'subscribed': subscribed.id}
        serializer = SubscriberSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'DELETE':
            subscribed_in.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        Subscriber.objects.create(user=current_user, subscribed=subscribed)
        serializer = SubscriptionUserSerializer(
            subscribed, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', ])
@permission_classes([permissions.AllowAny, ])
def user_get_token(request):
    """
    View предназначен для получения пользователем токена. При
    правильном имени пользователя и пароле система вернет токен, который
    необходимо указать для авторизации по методу Bearer.
    """
    absent_fields = []
    if request.data.get('password') is None:
        absent_fields.append('password')
    if request.data.get('email') is None:
        absent_fields.append('email')
    if len(absent_fields) != 0:
        return Response(
            {'Absent_fields': absent_fields},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = get_object_or_404(User, email=request.data['email'])
    if user.check_password(request.data['password']):
        token = AccessToken.for_user(user=user)
        return Response({
            'token': str(token),
        }, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', ])
def user_del_token(request):
    """
    View предназначен для удаления пользователем токена.
    """
    dt = datetime.now() + timedelta(days=20)
    token = jwt.encode({
        'id': request.user.id,
        'exp': dt.utcfromtimestamp(dt.timestamp())},
        settings.SECRET_KEY, algorithm='HS256')
    return Response({
        'token': str(token),
    }, status=status.HTTP_204_NO_CONTENT)


class MyAuthToken(auth_views.ObtainAuthToken):
    serializer_class = MyAuthTokenSerializer
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="email",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Email",
                        description="Valid email for authentication",
                    ),
                ),
                coreapi.Field(
                    name="password",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )


obtain_auth_token = MyAuthToken.as_view()