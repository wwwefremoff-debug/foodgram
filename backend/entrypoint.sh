#!/bin/sh
set -e

echo "Waiting for database..."
python <<'PY'
import os, time
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()
from django.db import connection
from django.db.utils import OperationalError

for i in range(30):
    try:
        connection.ensure_connection()
        print('Database is ready')
        break
    except OperationalError:
        print(f'Database unavailable, retry {i + 1}/30...')
        time.sleep(2)
else:
    raise SystemExit('Database not available')
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_ingredients || true
python manage.py shell <<'PY'
from recipes.models import Tag
for name, slug in (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
):
    Tag.objects.get_or_create(name=name, defaults={'slug': slug})
print('Tags ready:', Tag.objects.count())
PY

exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 60 foodgram.wsgi
