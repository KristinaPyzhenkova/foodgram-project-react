from django.contrib import admin

from .models import (
    User, Subscriber, Tag, Ingredient, Recipe,
    Amount, ShoppingCart, RecipeTag, Favorites
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'email',
                    'username',
                    'first_name',
                    'last_name')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'subscribed')
    search_fields = ('user',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'color',
                    'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'measurement_unit')
    search_fields = ('name', 'measurement_unit')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('counter',)
    list_display = ('id',
                    'author',
                    'name',
                    'image',
                    'text',
                    'cooking_time',
                    'counter')
    search_fields = ('author', 'name')

    def counter(self, obj):
        return obj.favoritess.count()
    counter.short_description = 'Счетчик добавления в избранное'


@admin.register(Amount)
class AmountAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'ingredients',
                    'recipes',
                    'amount')
    search_fields = ('recipes', 'amount')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'recipe')
    search_fields = ('user', 'recipe')


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipes',
                    'tags')
    empty_value_display = '-пусто-'


@admin.register(Favorites)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'recipes',
                    'user')
    empty_value_display = '-пусто-'
