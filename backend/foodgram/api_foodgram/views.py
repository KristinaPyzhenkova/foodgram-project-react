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

from .mixins import ListRetrieveViewSet
from .models import (Users, Subscribed, Tags, Ingredients,
                     Recipes, Amount, Shopping_cart, Favorites)
from .filter import RecipeFilter
from .serializers import (TagsSerializer, RecipesSerializer,
                          RecipesSerializerGet, FavoriteRecipesSerializer,
                          IngredientsSerializerGet, UserSerializer,
                          LiteRecipeSerializer, SubscriptionUserSerializer,
                          PasswordSerializer, NewUserSerializer)
from django.conf import settings
from .pagination import UsersPagination


@permission_classes([permissions.AllowAny, ])
class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Tags.
    Он позволяет получать данные о тэгах.
    """
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer


@permission_classes([permissions.IsAuthenticatedOrReadOnly, ])
class RecipesViewSet(viewsets.ModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Recipes.
    Он позволяет получать данные о рецептах, создавать, удалять и изменять их.
    Также добавлять рецепты в раздел "Избранное" или удалять их.
    Скачивать файл со списком покупок, добалять и удалять рецепты из него.
    Доступна фильтрация по избранному, автору, списку покупок и тегам.
    """
    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer
    pagination_class = UsersPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipesSerializerGet
        return RecipesSerializer

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def favorite(self, request, pk):
        current_user = self.request.user
        if current_user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        recipe = get_object_or_404(Recipes, pk=pk)
        recipe_in_favorite = Favorites.objects.filter(
            user=current_user, recipes=recipe
        )
        if request.method == 'POST':
            if recipe_in_favorite.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Favorites.objects.create(user=current_user, recipes=recipe)
            serializer = FavoriteRecipesSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not recipe_in_favorite.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            recipe_in_favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipes, pk=pk)
        current_user = self.request.user
        recipe_in_shop = Shopping_cart.objects.filter(
            user=current_user, recipe=recipe
        )
        if request.method == 'DELETE':
            if not recipe_in_shop.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            recipe_in_shop.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            if recipe_in_shop.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Shopping_cart.objects.create(user=current_user, recipe=recipe)
            serializer = LiteRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        shopping_list = {}
        ingredients = Amount.objects.filter(
            recipes__shopping__user=request.user).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(Sum('amount'))
        for ingredient in ingredients:
            amount = ingredient.get('amount__sum')
            name = ingredient.get('ingredients__name')
            measurement_unit = ingredient.get(
                'ingredients__measurement_unit'
            )
            shopping_list[name] = {
                'measurement_unit': measurement_unit,
                'amount': amount
            }
        main_list = ([f"{item}: {value['amount']}"
                      f" {value['measurement_unit']}\n"
                      for item, value in shopping_list.items()])
        response = HttpResponse(main_list, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="Cart.txt"'
        return response


@permission_classes([permissions.AllowAny, ])
class IngredientsViewSet(ListRetrieveViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Ingredients.
    Он позволяет получать данные обо всех ингредиентах
    или о каком-то определнном.
    """
    serializer_class = IngredientsSerializerGet
    queryset = Ingredients.objects.all()
    pagination_class = UsersPagination


@permission_classes([permissions.AllowAny, ])
class UsersViewSet(viewsets.ModelViewSet):
    """
    ViewSet предназначен для взаимодействия в моделью Users.
    Он позволяет получать данные о пользователях, о текущем пользователе(me),
    создавать пользователей и менять пароль, получать данные о подписках,
    подписываться и удалять подписки.
    """
    serializer_class = UserSerializer
    queryset = Users.objects.all()
    pagination_class = UsersPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return NewUserSerializer

    @action(
        detail=False,
        methods=('get',),
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
        methods=('POST',),
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def change_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        author = self.request.user
        print(serializer)
        if serializer.is_valid():
            if not author.check_password(
                    serializer.data.get("current_password")
            ):
                return Response(
                    {"current_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            author.set_password(serializer.data.get("new_password"))
            author.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully'
            }
            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('GET',),
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = Users.objects.filter(subscribed__user=request.user)
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
    def subscriptions_cr_del(self, request, pk):
        subscribed = get_object_or_404(Users, pk=pk)
        current_user = self.request.user
        subscribed_in = Subscribed.objects.filter(
            user=current_user, subscribed=subscribed
        )
        if request.method == 'DELETE':
            if not subscribed_in.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscribed_in.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'POST':
            if subscribed_in.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Subscribed.objects.create(user=current_user, subscribed=subscribed)
            serializer = SubscriptionUserSerializer(subscribed)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', ])
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
    user = get_object_or_404(Users, email=request.data['email'])
    if user.check_password(request.data['password']):
        token = AccessToken.for_user(user=user)
        return Response({
            'token': str(token),
        }, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', ])
def user_del_token(self):
    """
    View предназначен для удаления пользователем токена.
    """
    dt = datetime.now() + timedelta(days=20)
    token = jwt.encode({
        'id': self.user.id,
        'exp': dt.utcfromtimestamp(dt.timestamp())},
        settings.SECRET_KEY, algorithm='HS256')
    print(self)
    return Response({
        'token': str(token),
    }, status=status.HTTP_204_NO_CONTENT)
