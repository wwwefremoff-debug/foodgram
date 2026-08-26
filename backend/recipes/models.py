from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import BooleanField, Exists, OuterRef, Value

from foodgram.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_SHORT_CODE_LENGTH,
    MAX_TAG_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    STR_REPR_MAX_LENGTH,
)


class Tag(models.Model):
    """Тег рецепта."""

    name = models.CharField('Название', max_length=MAX_TAG_LENGTH, unique=True)
    slug = models.SlugField('Слаг', max_length=MAX_TAG_LENGTH, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:STR_REPR_MAX_LENGTH]


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField('Название', max_length=MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'[:STR_REPR_MAX_LENGTH]


class RecipeQuerySet(models.QuerySet):
    """QuerySet рецептов с флагами избранного и корзины."""

    def with_user_annotations(self, user):
        is_favorited = Value(False, output_field=BooleanField())
        is_in_shopping_cart = Value(False, output_field=BooleanField())
        if user.is_authenticated:
            is_favorited = Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk')),
            )
            is_in_shopping_cart = Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                ),
            )
        return self.annotate(
            is_favorited=is_favorited,
            is_in_shopping_cart=is_in_shopping_cart,
        ).order_by(*self.model._meta.ordering)


class Recipe(models.Model):
    """Рецепт."""

    objects = RecipeQuerySet.as_manager()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=MAX_RECIPE_NAME_LENGTH)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=(
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ),
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    short_code = models.CharField(
        'Код короткой ссылки',
        max_length=MAX_SHORT_CODE_LENGTH,
        unique=True,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:STR_REPR_MAX_LENGTH]


class RecipeIngredient(models.Model):
    """Ингредиент в рецепте с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT),
        ),
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.ingredient} — {self.amount}'[:STR_REPR_MAX_LENGTH]


class UserRecipeRelation(models.Model):
    """Абстрактная связь пользователя с рецептом."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_unique_user_recipe',
            ),
        )

    def __str__(self):
        return (
            f'{self.user} — {self.recipe} ({self._meta.verbose_name})'
            [:STR_REPR_MAX_LENGTH]
        )


class Favorite(UserRecipeRelation):
    """Избранный рецепт."""

    class Meta(UserRecipeRelation.Meta):
        abstract = False
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Рецепт в списке покупок."""

    class Meta(UserRecipeRelation.Meta):
        abstract = False
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
