from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .validators import validate_username, min_value_validator


class User(AbstractUser):
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


class Subscriber(models.Model):
    user = models.ForeignKey(
        User,
        related_name='user_subscribed',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    subscribed = models.ForeignKey(
        User,
        related_name='subscribed',
        on_delete=models.CASCADE,
        verbose_name='Подписывающийся'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name='Название тега',
        db_index=True
    )
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет тега',
        db_index=True
    )
    slug = models.SlugField(
        unique=True, max_length=50,
        db_index=True, verbose_name='Ссылка на тег'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тег'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
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
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[min_value_validator]
    )
    favorite = models.ManyToManyField(
        User,
        through='Favorite'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tags = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipes', 'tags'],
                name='unique recipe_tag'
            )
        ]

    def __str__(self):
        return f'{self.recipes} {self.tags}'


class Favorite(models.Model):
    recipes = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favoritess'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favoritess'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipes', 'user'],
                name='unique favorite'
            )
        ]


class Amount(models.Model):
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='amount'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='amount'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Кол-во ингредиента',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return f'{self.amount}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping',
        on_delete=models.CASCADE,
        verbose_name='Покупатель'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping',
        on_delete=models.CASCADE,
        verbose_name='Рецепт для покупок'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Карта покупок'
        verbose_name_plural = 'Карты покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique shopping_cart'
            )
        ]
