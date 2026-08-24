from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from recipes.models import Favorite, ShoppingCart


def annotate_recipe_flags(queryset, user):
    """Добавить is_favorited и is_in_shopping_cart одним запросом."""
    if user is not None and user.is_authenticated:
        return queryset.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                )
            ),
        )
    return queryset.annotate(
        is_favorited=Value(False, output_field=BooleanField()),
        is_in_shopping_cart=Value(False, output_field=BooleanField()),
    )


def with_recipes_count(queryset):
    """Аннотировать queryset пользователей числом рецептов."""
    return queryset.annotate(recipes_count=Count('recipes'))
