from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


DEMO_RECIPES = (
    (
        'chef',
        'Борщ со сметаной',
        'Классический борщ со свёклой, капустой и сметаной.',
        60,
        (140, 40, 40),
        (210, 120, 90),
    ),
    (
        'chef',
        'Пельмени домашние',
        'Пельмени с говядиной и свининой, подаются со сметаной.',
        90,
        (180, 150, 110),
        (230, 210, 180),
    ),
    (
        'chef',
        'Оливье',
        'Праздничный салат оливье с варёными овощами и колбасой.',
        40,
        (90, 140, 70),
        (170, 200, 120),
    ),
    (
        'chef',
        'Сырники',
        'Сырники из творога со сметаной и вареньем.',
        25,
        (210, 170, 80),
        (245, 220, 150),
    ),
    (
        'baker',
        'Шарлотка',
        'Яблочная шарлотка на кефире.',
        50,
        (160, 100, 50),
        (220, 170, 100),
    ),
    (
        'baker',
        'Блины',
        'Тонкие блины на молоке.',
        30,
        (190, 130, 60),
        (235, 190, 120),
    ),
    (
        'cook',
        'Гречка с грибами',
        'Гречневая каша с жареными грибами и луком.',
        35,
        (110, 70, 40),
        (170, 120, 70),
    ),
)


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

        created_recipes = 0
        updated_images = 0
        refresh = options['refresh_images']
        for (
            username,
            name,
            text,
            cooking_time,
            color_top,
            color_bottom,
        ) in DEMO_RECIPES:
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
                recipe.image.save(
                    f'{recipe.pk}.jpg',
                    self._image(name, color_top, color_bottom),
                    save=True,
                )
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
    def _image(title, color_top, color_bottom):
        width, height = 640, 480
        image = Image.new('RGB', (width, height), color_top)
        draw = ImageDraw.Draw(image)
        for y in range(height):
            ratio = y / height
            color = tuple(
                int(color_top[i] * (1 - ratio) + color_bottom[i] * ratio)
                for i in range(3)
            )
            draw.line((0, y, width, y), fill=color)
        plate = (90, 70, 550, 410)
        draw.ellipse(
            plate,
            fill=(245, 240, 230),
            outline=(220, 210, 195),
            width=4,
        )
        food = (160, 130, 480, 350)
        draw.ellipse(food, fill=color_top, outline=color_bottom, width=3)
        draw.ellipse((250, 180, 390, 300), fill=color_bottom)
        font = ImageFont.load_default()
        text = title
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.rectangle(
            (20, height - 60, width - 20, height - 20),
            fill=(30, 30, 30),
        )
        draw.text(
            ((width - text_width) // 2, height - 48),
            text,
            fill=(255, 255, 255),
            font=font,
        )
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return ContentFile(buffer.read(), name='recipe.jpg')
