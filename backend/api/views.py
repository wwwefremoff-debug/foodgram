import secrets
from io import BytesIO

from django.db.models import F, Sum
from django.http import FileResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    SetAvatarSerializer,
    ShoppingCartSerializer,
    SubscriptionCreateSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from api.shopping_list import format_shopping_list
from foodgram.constants import SHORT_CODE_LENGTH
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class UserViewSet(DjoserUserViewSet):
    """Пользователи, аватар и подписки."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        serializer = SetAvatarSerializer(
            request.user,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscriptions_to_author__user=request.user,
        ).with_recipes_count()
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context=self.get_serializer_context(),
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        get_object_or_404(User, id=id)
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author_id=id,
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        ) if deleted else Response(
            {'errors': 'Вы не были подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и получение тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и получение ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD рецептов, избранное, корзина, короткие ссылки."""

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'recipe_ingredients__ingredient',
        )
        return queryset.with_user_annotations(self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def _add_relation(self, serializer_class, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_relation(self, model, request, pk, missing_message):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        ) if deleted else Response(
            {'errors': missing_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._add_relation(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._remove_relation(
            Favorite,
            request,
            pk,
            'Рецепта нет в избранном.',
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        return self._add_relation(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._remove_relation(
            ShoppingCart,
            request,
            pk,
            'Рецепта нет в списке покупок.',
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart_set__user=request.user,
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit'),
        ).annotate(
            total=Sum('amount'),
        ).order_by('name')
        content = format_shopping_list(ingredients)
        buffer = BytesIO(content.encode('utf-8'))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
        )

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if not recipe.short_code:
            recipe.short_code = secrets.token_urlsafe(4)[:SHORT_CODE_LENGTH]
            recipe.save(update_fields=['short_code'])
        short_path = reverse(
            'recipe-short-link',
            kwargs={'short_code': recipe.short_code},
        )
        short_link = request.build_absolute_uri(short_path)
        return Response({'short-link': short_link})


class RecipeShortLinkRedirectView(APIView):
    """Редирект с короткой ссылки на страницу рецепта."""

    permission_classes = (AllowAny,)

    def get(self, request, short_code):
        recipe = Recipe.objects.filter(short_code=short_code).first()
        if recipe is None:
            url = request.build_absolute_uri('/not_found')
        else:
            url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return HttpResponsePermanentRedirect(url)
