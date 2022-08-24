from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .validators import validate_username, min_value_validator


class Users(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    email = models.EmailField(
        _('email'),
        max_length=254,
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    username = models.CharField(
        _('Имя пользователя'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer.'
            'Letters, digits and @/./+/-/_ only.'
        ),
        validators=[username_validator, validate_username],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(
        _('Имя'),
        max_length=150,
    )
    last_name = models.CharField(
        _('Фамилия'),
        max_length=150,
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribed(models.Model):
    user = models.ForeignKey(
        Users,
        related_name='user_subscribed',
        on_delete=models.SET_DEFAULT,
        default=False,
        verbose_name='Подписчик'
    )
    subscribed = models.ForeignKey(
        Users,
        related_name='subscribed',
        on_delete=models.SET_DEFAULT,
        default=False,
        verbose_name='Подписывающийся'
    )


class Tags(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название тега',
        db_index=True
    )
    color = models.CharField(
        max_length=256,
        verbose_name='Цвет тега',
        db_index=True
    )
    slug = models.SlugField(
        unique=True, max_length=50,
        db_index=True, verbose_name='Ссылка на тег'
    )

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    Kg = 'kg'
    Gram = 'gram'
    Milligram = 'milligram'
    Liter = 'liter'
    Count = 'count'
    Taste = 'taste'
    Tea_spoon = 'tea_spoon'
    Spoon = 'spoon'
    Drop = 'drop'
    Piece = 'piece'
    measurement = [
        (Kg, 'кг'),
        (Gram, 'г'),
        (Milligram, 'мл'),
        (Liter, 'л'),
        (Count, 'шт'),
        (Taste, 'по вкусу'),
        (Tea_spoon, 'ч. л.'),
        (Spoon, 'ст. л.'),
        (Spoon, 'ст. л.'),
        (Drop, 'капля'),
        (Piece, 'кусок'),
    ]
    name = models.CharField(
        max_length=256,
        verbose_name='Название ингредиента',
        db_index=True
    )
    measurement_unit = models.CharField(
        max_length=10,
        choices=measurement,
        default=Gram,
        verbose_name='Ед. измерения',
    )

    def __str__(self):
        return self.name


class Recipes(models.Model):
    tags = models.ManyToManyField(
        Tags,
        through='RecipesTags',
        verbose_name='Тег'
    )
    author = models.ForeignKey(
        Users,
        related_name='recipe',
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='Amount'
    )
    name = models.TextField(
        verbose_name='Название',
        db_index=True,
        max_length=200)
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True
    )
    text = models.TextField(
        verbose_name='Текст',
        max_length=256
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[min_value_validator]
    )
    favorite = models.ManyToManyField(
        Users,
        through='Favorites'
    )

    def __str__(self):
        return self.name


class RecipesTags(models.Model):
    recipes = models.ForeignKey(Recipes, on_delete=models.CASCADE)
    tags = models.ForeignKey(Tags, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.recipes} {self.tags}'


class Favorites(models.Model):
    recipes = models.ForeignKey(
        Recipes, on_delete=models.CASCADE,
        related_name='favoritess', blank=True
    )
    user = models.ForeignKey(
        Users, on_delete=models.CASCADE,
        related_name='favoritess', blank=True
    )


class Amount(models.Model):
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='amount_r'
    )
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='amount_r'
    )
    amount = models.IntegerField(
        verbose_name='Кол-во ингредиента',
    )

    def __str__(self):
        return f'{self.amount}'


class Shopping_cart(models.Model):
    user = models.ForeignKey(
        Users,
        related_name='shopping',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Покупатель'
    )
    recipe = models.ForeignKey(
        Recipes,
        related_name='shopping',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Рецепт для покупок'
    )
