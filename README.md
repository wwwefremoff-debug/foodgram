# Foodgram

[![CI](https://github.com/wwwefremoff-debug/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/wwwefremoff-debug/foodgram/actions/workflows/main.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

**Сайт проекта:** [http://158.160.132.25.sslip.io/](http://158.160.132.25.sslip.io/)

Foodgram — сервис для публикации кулинарных рецептов. Пользователи регистрируются, публикуют рецепты с фото, ингредиентами и тегами, подписываются на авторов, добавляют рецепты в избранное и формируют список покупок, который можно скачать файлом.

API соответствует спецификации OpenAPI: `docs/openapi-schema.yml`.

Документация API (ReDoc): [http://158.160.132.25.sslip.io/api/docs/](http://158.160.132.25.sslip.io/api/docs/)

## Возможности

- Регистрация и авторизация по email (Token Authentication)
- Профиль пользователя с аватаром
- CRUD рецептов: название, описание, картинка, время приготовления, теги, ингредиенты
- Фильтрация рецептов по тегам, автору, избранному и списку покупок
- Подписки на авторов с превью их рецептов
- Избранное и список покупок
- Короткие ссылки на рецепты
- Админка Django

## Стек

- Python 3.12, Django 5, Django REST Framework, Djoser, django-filter
- PostgreSQL, Gunicorn, Nginx, Docker Compose
- Frontend — готовая сборка Яндекс Практикума
- CI/CD — GitHub Actions + Docker Hub

## Переменные окружения

Скопируйте пример и заполните значения:

```bash
cp infra/.env.example infra/.env
```

| Переменная | Описание |
| --- | --- |
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | `False` в продакшене |
| `ALLOWED_HOSTS` | Хосты через запятую, например `localhost,127.0.0.1,158.160.132.25.sslip.io` |
| `CSRF_TRUSTED_ORIGINS` | Доверенные origin через запятую, с `http://` |
| `POSTGRES_DB` | Имя базы данных |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `DB_ENGINE` | `django.db.backends.postgresql` |
| `DB_HOST` | Хост БД (`db` в Docker) |
| `DB_PORT` | Порт БД (`5432`) |
| `DOCKER_USERNAME` | Логин Docker Hub для production-образа |

## Локальный запуск (SQLite)

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_ingredients
python manage.py createsuperuser
python manage.py runserver
```

Команда `load_ingredients` загружает ингредиенты из `data/ingredients.json`.

Перед проверкой Postman создайте в админке минимум 3 тега.

- API: http://127.0.0.1:8000/api/
- Админка: http://127.0.0.1:8000/admin/

## Запуск через Docker Compose

```bash
cp infra/.env.example infra/.env
cd infra
docker compose up -d --build
```

После первого запуска создайте суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

Ингредиенты подгружаются при старте контейнера (`entrypoint.sh`). Если нужно загрузить повторно:

```bash
docker compose exec backend python manage.py load_ingredients
```

- Сайт: http://localhost/
- API docs: http://localhost/api/docs/
- Админка: http://localhost/admin/

## Деплой на сервер

1. Установите Docker и Docker Compose.
2. Клонируйте репозиторий.
3. Заполните `infra/.env` (`SECRET_KEY`, `ALLOWED_HOSTS`, пароли БД).
4. Запустите стек:

```bash
cd infra
docker compose up -d --build
```

Для production-образа backend укажите `DOCKER_USERNAME` в `.env` и используйте:

```bash
docker compose -f docker-compose.production.yml up -d --build
```

В GitHub Secrets добавьте:

- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `HOST`, `USER`, `SSH_KEY`

Workflow `.github/workflows/main.yml` при пуше в `main`/`master` проверяет проект, собирает образ backend и деплоит его на VPS.

## Структура проекта

```
backend/              — Django API
frontend/             — React (Яндекс Практикум)
infra/                — docker-compose, nginx, .env
docs/                 — OpenAPI / ReDoc
data/                 — ingredients.json
postman_collection/   — коллекция для проверки API
```

## Автор

Сергей Ефремов

- GitHub: [wwwefremoff-debug](https://github.com/wwwefremoff-debug)
- Проект: [foodgram](https://github.com/wwwefremoff-debug/foodgram)
