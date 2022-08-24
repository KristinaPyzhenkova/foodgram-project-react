from rest_framework.routers import SimpleRouter
from django.urls import include, path
from .views import (TagsViewSet, RecipesViewSet, IngredientsViewSet,
                    UsersViewSet, user_get_token, user_del_token)
from django.conf import settings
from django.conf.urls.static import static


router = SimpleRouter()
router.register('tags', TagsViewSet)
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientsViewSet)
router.register('users', UsersViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', user_get_token, name='token'),
    path('auth/token/logout/', user_del_token, name='token_del'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
