from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.annotations import annotate_recipe_flags, with_recipes_count
from foodgram.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с is_subscribed и avatar."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(DjoserUserSerializer.Meta.fields) + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.user_subscriptions.filter(author=obj).exists()
        )


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор загрузки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Ингредиент в составе рецепта (чтение)."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Ингредиент при создании/обновлении рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'min_value': f'Количество должно быть не меньше {MIN_AMOUNT}.',
            'max_value': f'Количество должно быть не больше {MAX_AMOUNT}.',
            'invalid': 'Введите целое число.',
        },
    )


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта (чтение)."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецепта."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        error_messages={
            'min_value': (
                f'Время приготовления должно быть не меньше '
                f'{MIN_COOKING_TIME}.'
            ),
            'max_value': (
                f'Время приготовления должно быть не больше '
                f'{MAX_COOKING_TIME}.'
            ),
            'invalid': 'Введите целое число.',
        },
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент.',
            )
        ingredient_ids = [
            ingredient['id'].id for ingredient in ingredients
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.',
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return tags

    def validate_image(self, image):
        if not image and self.instance is None:
            raise serializers.ValidationError('Обязательное поле.')
        return image

    @staticmethod
    def _set_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._set_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        recipe = annotate_recipe_flags(
            Recipe.objects.filter(pk=instance.pk),
            user,
        ).first()
        return RecipeSerializer(recipe, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    """Пользователь с рецептами для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request is not None:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None:
                try:
                    recipes = recipes[:int(recipes_limit)]
                except (TypeError, ValueError):
                    pass
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Создание подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'},
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
            )
        return attrs

    def to_representation(self, instance):
        author = with_recipes_count(User.objects.all()).get(
            pk=instance.author_id,
        )
        return UserWithRecipesSerializer(
            author,
            context=self.context,
        ).data


class RecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор связи пользователь-рецепт."""

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, attrs):
        if self.Meta.model.objects.filter(**attrs).exists():
            raise serializers.ValidationError(
                {'errors': self.error_message},
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data


class FavoriteSerializer(RecipeRelationSerializer):
    """Добавление рецепта в избранное."""

    error_message = 'Рецепт уже в избранном.'

    class Meta(RecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(RecipeRelationSerializer):
    """Добавление рецепта в список покупок."""

    error_message = 'Рецепт уже в списке покупок.'

    class Meta(RecipeRelationSerializer.Meta):
        model = ShoppingCart
