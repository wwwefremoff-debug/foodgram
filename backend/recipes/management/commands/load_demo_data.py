from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


DEMO_RECIPES = (
    (
        'chef',
        'Борщ со сметаной',
        'Классический борщ со свёклой, капустой и сметаной.',
        60,
        'borscht.jpg',
    ),
    (
        'chef',
        'Пельмени домашние',
        'Пельмени с говядиной и свининой, подаются со сметаной.',
        90,
        'pelmeni.jpg',
    ),
    (
        'chef',
        'Оливье',
        'Праздничный салат оливье с варёными овощами и колбасой.',
        40,
        'olivier.jpg',
    ),
    (
        'chef',
        'Сырники',
        'Сырники из творога со сметаной и вареньем.',
        25,
        'syrniki.jpg',
    ),
    (
        'baker',
        'Шарлотка',
        'Яблочная шарлотка на кефире.',
        50,
        'charlotte.jpg',
    ),
    (
        'baker',
        'Блины',
        'Тонкие блины на молоке.',
        30,
        'blini.jpg',
    ),
    (
        'cook',
        'Гречка с грибами',
        'Гречневая каша с жареными грибами и луком.',
        35,
        'buckwheat.jpg',
    ),
)

EXTRA_IMAGES = {
    'Салат из огурцов и помидоров': 'salad.jpg',
    'Омлет': 'omelette.jpg',
    'Овсянка на молоке': 'oatmeal.jpg',
}


class Command(BaseCommand):
    """Демо-пользователи и рецепты для ревью."""

    help = 'Создать администратора review и минимум 7 рецептов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh-images',
            action='store_true',
            help='Обновить картинки у демо-рецептов',
        )

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

        images_dir = self._images_dir()
        if images_dir is None:
            self.stdout.write(
                self.style.ERROR('Не найдена папка data/recipe_images'),
            )
            return

        created_recipes = 0
        updated_images = 0
        refresh = options['refresh_images']
        for username, name, text, cooking_time, image_name in DEMO_RECIPES:
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                author=authors[username],
                defaults={
                    'text': text,
                    'cooking_time': cooking_time,
                },
            )
            if created:
                recipe.tags.set(tags[:2])
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={'amount': 100},
                )
                created_recipes += 1
            if created or refresh or not recipe.image:
                if self._set_image(recipe, images_dir / image_name):
                    updated_images += 1

        for recipe_name, image_name in EXTRA_IMAGES.items():
            for recipe in Recipe.objects.filter(name=recipe_name):
                if refresh or not recipe.image:
                    if self._set_image(recipe, images_dir / image_name):
                        updated_images += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Админ: {review.email}. Рецептов создано: '
                f'{created_recipes}. Картинок обновлено: {updated_images}. '
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
    def _images_dir():
        candidates = [
            Path('/app/data/recipe_images'),
        ]
        base = Path(__file__).resolve()
        for depth in (4, 5):
            if len(base.parents) > depth:
                candidates.append(
                    base.parents[depth] / 'data' / 'recipe_images',
                )
        for path in candidates:
            if path.is_dir():
                return path
        return None

    @staticmethod
    def _set_image(recipe, path):
        if not path.exists():
            return False
        with path.open('rb') as image_file:
            recipe.image.save(path.name, File(image_file), save=True)
        return True
