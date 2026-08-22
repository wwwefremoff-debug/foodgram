# Foodgram

Дипломный проект Яндекс Практикума: сайт для публикации рецептов, подписок, избранного и списка покупок.

API реализован по спецификации `docs/openapi-schema.yml`.

## Стек

- Python 3.12 / Django 5 / DRF / Djoser
- PostgreSQL / Docker / Nginx / Gunicorn
- Frontend — готовая сборка Практикума
- CI/CD — GitHub Actions + Docker Hub

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

Перед Postman создайте минимум 3 тега в админке.

## Docker Compose (локально)

```bash
cp infra/.env.example infra/.env
# при необходимости отредактируйте infra/.env
cd infra
docker compose up -d --build
```

- Frontend: http://localhost/
- API docs: http://localhost/api/docs/
- Admin: http://localhost/admin/ (после `createsuperuser`)

Создать суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Деплой на сервер

1. На сервере установите Docker и Docker Compose.
2. Скопируйте `infra/`, `docs/`, `data/`, `frontend/` (или соберите frontend отдельно).
3. Заполните `.env` (SECRET_KEY, ALLOWED_HOSTS=IP_сервера, пароли БД).
4. Для production-образа backend укажите `DOCKER_USERNAME` в `.env` и используйте:

```bash
docker compose -f docker-compose.production.yml up -d --build
```

5. В GitHub Secrets добавьте:
   - `DOCKER_USERNAME`, `DOCKER_PASSWORD`
   - `HOST`, `USER`, `SSH_KEY`

Workflow `.github/workflows/main.yml` при пуше в `main`/`master`:
проверяет проект → собирает и пушит образ backend → деплоит на VPS.

## Адрес сервера

Проект доступен по адресу: http://158.160.132.25/

## Структура

```
backend/     — Django API
frontend/    — React (Практикум)
infra/       — docker-compose, nginx, .env
docs/        — OpenAPI / ReDoc
data/        — ingredients.json
postman_collection/ — коллекция для проверки API
```
