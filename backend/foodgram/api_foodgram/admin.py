from django.contrib import admin

from .models import (Users, Subscribed, Tags, Ingredients, Recipes,
                     Amount, Shopping_cart, RecipesTags, Favorites)


class UsersAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'email',
                    'username',
                    'first_name',
                    'last_name')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


class SubscribedAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'subscribed')
    search_fields = ('user',)
    empty_value_display = '-пусто-'


class TagsAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'color',
                    'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'measurement_unit')
    search_fields = ('name', 'measurement_unit')


class RecipesAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'author',
                    'name',
                    'image',
                    'text',
                    'cooking_time')
    search_fields = ('author', 'name')


class AmountAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'ingredients',
                    'recipes',
                    'amount')
    search_fields = ('recipes', 'amount')


class Shopping_cartAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'recipe')
    search_fields = ('user', 'recipe')


class RecipesTagsAdmin(admin.ModelAdmin):
    list_display = ('recipes',
                    'tags')
    empty_value_display = '-пусто-'


class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'recipes',
                    'user')
    empty_value_display = '-пусто-'


admin.site.register(Users, UsersAdmin)
admin.site.register(Subscribed, SubscribedAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Tags, TagsAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(Amount, AmountAdmin)
admin.site.register(Shopping_cart, Shopping_cartAdmin)
admin.site.register(RecipesTags, RecipesTagsAdmin)
admin.site.register(Favorites, FavoritesAdmin)
