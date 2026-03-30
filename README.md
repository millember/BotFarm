# BotFarm Service

Сервис для управления пользователями в ботоферме. Предоставляет REST API для создания, получения, блокировки, разблокировки и удаления пользователей.

## Функционал

- Создание пользователя с хешированием пароля
- Получение списка всех пользователей
- Блокировка пользователя для E2E тестов
- Разблокировка всех пользователей
- Удаление пользователя

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL 14
- Pydantic
- Poetry
- Docker / Docker Compose
- Pytest (покрытие 85%+)

## Быстрый старт

### Через Docker (рекомендуется)

```bash
git clone git@github.com:millember/BotFarm.git
cd botfarm
docker-compose up --build
```

### Локальный запуск

```bash
# Установить Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -
# или через brew: brew install poetry

# Установить зависимости
poetry install

# Запустить PostgreSQL в Docker
docker-compose up -d db

# Запустить приложение
poetry run uvicorn main:botfarm --reload
```

## API Эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/users` | Создать пользователя |
| GET | `/users` | Получить всех пользователей |
| POST | `/users/lock` | Заблокировать свободного пользователя |
| POST | `/users/unlock` | Разблокировать всех пользователей |
| DELETE | `/users/{user_id}` | Удалить пользователя |
| GET | `/health` | Проверка здоровья сервиса |
| GET | `/` | Корневой эндпоинт |

## Примеры запросов

### Создание пользователя

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "login": "user@example.com",
    "password": "secure_password",
    "project_id": "123e4567-e89b-12d3-a456-426614174000",
    "env": "prod",
    "domain": "regular"
  }'
```

### Блокировка пользователя

```bash
curl -X POST http://localhost:8000/users/lock
```

### Получение списка пользователей

```bash
curl http://localhost:8000/users
```

## Документация API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Запуск тестов

```bash
# В Docker
docker-compose exec app pytest tests/test_basic.py -v --cov=. --cov-report=term

# Локально с Poetry
poetry run pytest tests/test_basic.py -v --cov=. --cov-report=term
```

## Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| DATABASE_URL | `postgresql+asyncpg://oppennec:password@db:5432/botfarm` | URL подключения к БД |
| SQL_ECHO | `false` | Логирование SQL запросов |

## Структура проекта

```
botfarm/
├── main.py                 # FastAPI приложение (роутеры)
├── models.py               # SQLAlchemy модели
├── schemas.py              # Pydantic схемы
├── auth.py                 # Хеширование паролей
├── database.py             # Подключение к БД
├── config.py               # Конфигурация (таймзона, SQL)
├── services/
│   └── users.py            # Бизнес-логика
├── tests/
│   ├── conftest.py         # Фикстуры для тестов
│   └── test_basic.py       # Тесты
├── pyproject.toml          # Конфигурация Poetry
├── poetry.lock             # Фиксация версий
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Требования

- Python 3.12+
- Poetry
- Docker (опционально)
- PostgreSQL 14+ (для локального запуска)

## Лицензия

MIT
```