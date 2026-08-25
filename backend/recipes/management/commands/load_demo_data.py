from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


DEMO_RECIPES = (
    (
        'chef',
        'Борщ со сметаной',
        'Классический борщ со свёклой, капустой и сметаной.',
        60,
    ),
    (
        'chef',
        'Пельмени домашние',
        'Пельмени с говядиной и свининой, подаются со сметаной.',
        90,
    ),
    (
        'chef',
        'Оливье',
        'Праздничный салат оливье с варёными овощами и колбасой.',
        40,
    ),
    (
        'chef',
        'Сырники',
        'Сырники из творога со сметаной и вареньем.',
        25,
    ),
    (
        'baker',
        'Шарлотка',
        'Яблочная шарлотка на кефире.',
        50,
    ),
    (
        'baker',
        'Блины',
        'Тонкие блины на молоке.',
        30,
    ),
    (
        'cook',
        'Гречка с грибами',
        'Гречневая каша с жареными грибами и луком.',
        35,
    ),
)


class Command(BaseCommand):
    """Демо-пользователи и рецепты для ревью."""

    help = 'Создать администратора review и минимум 7 рецептов'

    def handle(self, *args, **options):
        review = self._user(
            username='review',
            email='review@admin.ru',
            password='review1admin',
            first_name='Review',
            last_name='Admin',
            is_staff=True,
            is_superuser=True,
        )
        chef = self._user(
            username='chef',
            email='chef@foodgram.ru',
            password='FoodgramPass_26',
            first_name='Иван',
            last_name='Шеф',
        )
        baker = self._user(
            username='baker',
            email='baker@foodgram.ru',
            password='FoodgramPass_26',
            first_name='Анна',
            last_name='Пекарь',
        )
        cook = self._user(
            username='cook',
            email='cook@foodgram.ru',
            password='FoodgramPass_26',
            first_name='Олег',
            last_name='Повар',
        )
        authors = {
            'chef': chef,
            'baker': baker,
            'cook': cook,
        }
        tags = self._tags()
        ingredient = Ingredient.objects.first()
        if ingredient is None:
            self.stdout.write(
                self.style.ERROR('Сначала загрузите ингредиенты'),
            )
            return

        created_recipes = 0
        for username, name, text, cooking_time in DEMO_RECIPES:
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                author=authors[username],
                defaults={
                    'text': text,
                    'cooking_time': cooking_time,
                },
            )
            if created:
                recipe.image.save(
                    f'{recipe.pk}.jpg',
                    self._image(),
                    save=True,
                )
                recipe.tags.set(tags[:2])
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={'amount': 100},
                )
                created_recipes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Админ: {review.email}. Рецептов создано: {created_recipes}. '
                f'Всего рецептов: {Recipe.objects.count()}.'
            )
        )

    def _user(self, **kwargs):
        password = kwargs.pop('password')
        extra = {
            'is_staff': kwargs.pop('is_staff', False),
            'is_superuser': kwargs.pop('is_superuser', False),
        }
        user, created = User.objects.get_or_create(
            email=kwargs['email'],
            defaults=kwargs,
        )
        user.first_name = kwargs['first_name']
        user.last_name = kwargs['last_name']
        user.username = kwargs['username']
        user.is_staff = extra['is_staff'] or user.is_staff
        user.is_superuser = extra['is_superuser'] or user.is_superuser
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def _tags():
        names = (
            ('Завтрак', 'breakfast'),
            ('Обед', 'lunch'),
            ('Ужин', 'dinner'),
        )
        tags = []
        for name, slug in names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={'slug': slug},
            )
            tags.append(tag)
        return tags

    @staticmethod
    def _image():
        buffer = BytesIO()
        Image.new('RGB', (400, 300), (210, 90, 70)).save(buffer, format='JPEG')
        buffer.seek(0)
        return ContentFile(buffer.read(), name='recipe.jpg')
