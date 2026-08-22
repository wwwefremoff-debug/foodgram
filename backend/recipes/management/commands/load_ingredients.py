import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов из data/ingredients.json."""

    help = 'Импорт ингредиентов из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='Путь к ingredients.json',
        )

    def handle(self, *args, **options):
        path = options['path']
        if path is None:
            candidates = [
                Path('/app/data/ingredients.json'),
                Path(__file__).resolve().parents[4]
                / 'data'
                / 'ingredients.json',
            ]
            path = next((p for p in candidates if p.exists()), candidates[-1])
        else:
            path = Path(path)

        with open(path, encoding='utf-8') as file:
            data = json.load(file)

        ingredients = [
            Ingredient(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            for item in data
        ]
        created = Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено ингредиентов: {len(created)} '
                f'(файл: {path})'
            )
        )
