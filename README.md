# BotFarm Service

Сервис для управления пользователями в ботоферме. Предоставляет REST API для создания, получения, блокировки, разблокировки и удаления пользователей.

## Функционал

- Создание пользователя с хешированием пароля (Argon2)
- Получение списка всех пользователей
- Блокировка пользователя для E2E тестов (с автоматическим снятием блокировки)
- Разблокировка всех пользователей
- Удаление пользователя
- Healthchecks для Kubernetes/оркестрации

## Технологии

- **Python** 3.12
- **FastAPI** — веб-фреймворк
- **SQLAlchemy** 2.0 — ORM (асинхронный)
- **PostgreSQL** 14 — база данных
- **Pydantic** — валидация данных
- **Argon2** — хеширование паролей
- **Poetry** — управление зависимостями
- **Docker** / **Docker Compose** — контейнеризация
- **Pytest** — тестирование (покрытие 88%+)

## Быстрый старт

### Через Docker (рекомендуется)

```bash
git clone git@github.com:millember/BotFarm.git
cd botfarm

# Создать .env файл
cat > .env << EOF
POSTGRES_USER=oppennec
POSTGRES_PASSWORD=password
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=botfarm
DEBUG=false
SQL_ECHO=false
LOCK_DURATION_MINUTES=30
EOF

# Запустить
docker-compose up --build
```

### Локальный запуск

```bash
# Установить Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установить зависимости
poetry install

# Запустить PostgreSQL в Docker
docker-compose up -d db

# Создать .env для локального запуска
cat > .env << EOF
POSTGRES_USER=oppennec
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=botfarm
DEBUG=true
SQL_ECHO=true
LOCK_DURATION_MINUTES=30
EOF

# Запустить приложение
poetry run uvicorn main:botfarm --reload
```

## API Эндпоинты

| Метод | Эндпоинт | Описание | Статусы ответа |
|-------|----------|----------|----------------|
| POST | `/users` | Создать пользователя | 201, 409 |
| GET | `/users` | Получить всех пользователей | 200 |
| POST | `/users/lock` | Заблокировать свободного пользователя | 200, 404 |
| POST | `/users/unlock` | Разблокировать всех пользователей | 200 |
| DELETE | `/users/{user_id}` | Удалить пользователя | 200, 404 |
| GET | `/health` | Проверка здоровья сервиса | 200, 503 |
| GET | `/ready` | Readiness probe | 200, 503 |
| GET | `/live` | Liveness probe | 200 |
| GET | `/` | Корневой эндпоинт | 200 |

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

**Ответ (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00+03:00",
  "login": "user@example.com",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "env": "prod",
  "domain": "regular",
  "locktime": null
}
```

### Блокировка пользователя

```bash
curl -X POST http://localhost:8000/users/lock
```

**Ответ (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00+03:00",
  "login": "user@example.com",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "env": "prod",
  "domain": "regular",
  "locktime": "2024-01-15T10:35:00+03:00"
}
```

### Получение списка пользователей

```bash
curl http://localhost:8000/users
```

### Разблокировка всех пользователей

```bash
curl -X POST http://localhost:8000/users/unlock
```

**Ответ:**
```json
{
  "message": "Unlocked 5 users"
}
```

### Удаление пользователя

```bash
curl -X DELETE http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000
```

**Ответ:**
```json
{
  "message": "User 550e8400-e29b-41d4-a716-446655440000 deleted"
}
```

## Модели данных

### User (модель БД)

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | Уникальный идентификатор |
| login | EmailStr | Email пользователя (уникальный) |
| password | str | Хеш пароля (Argon2) |
| project_id | UUID | ID проекта |
| env | enum | Окружение: `prod`, `stage`, `preriod` |
| domain | enum | Домен: `canary`, `regular` |
| created_at | datetime | Дата создания (MSK) |
| locktime | datetime | Время блокировки (MSK) |

## Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| POSTGRES_USER | oppennec | Пользователь БД |
| POSTGRES_PASSWORD | password | Пароль БД |
| POSTGRES_HOST | db | Хост БД |
| POSTGRES_PORT | 5432 | Порт БД |
| POSTGRES_DB | botfarm | Имя БД |
| APP_NAME | BotFarm | Имя приложения |
| DEBUG | false | Режим отладки |
| SQL_ECHO | false | Логирование SQL запросов |
| LOCK_DURATION_MINUTES | 30 | Длительность блокировки (минут) |

## Документация API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Запуск тестов

### В Docker
```bash
docker-compose exec app pytest -v --cov=. --cov-report=term
```

### Локально с Poetry
```bash
poetry run pytest -v --cov=. --cov-report=term
```

### Покрытие тестами: 88%+

```
Name                           Stmts   Miss  Cover
--------------------------------------------------
auth.py                            4      0   100%
config.py                         21      0   100%
database.py                       13      0   100%
main.py                           32      5    84%
models.py                         12      0   100%
repositories/users.py             31      4    87%
routes/users.py                   24      0   100%
schemas.py                        13      0   100%
services/users.py                 31      0   100%
--------------------------------------------------
TOTAL                            181     10    94% (с тестами 88%+)
```

## Структура проекта

```
botfarm/
├── main.py                 # FastAPI приложение (роутеры, lifespan)
├── models.py               # SQLAlchemy модели
├── schemas.py              # Pydantic схемы (DTO)
├── auth.py                 # Хеширование паролей
├── database.py             # Подключение к БД
├── config.py               # Конфигурация (env переменные)
├── repositories/           # Слой доступа к данным
│   └── users.py            # CRUD операции с User
├── services/               # Бизнес-логика
│   └── users.py            # UserService
├── routes/                 # API роутеры
│   └── users.py            # Эндпоинты /users
├── tests/                  # Тесты
│   ├── conftest.py         # Фикстуры (клиент, БД)
│   └── test_basic.py       # 88% покрытия
├── .env                    # Переменные окружения (не в git)
├── .env.example            # Пример env файла
├── docker-compose.yml      # Docker Compose
├── Dockerfile              # Docker образ
├── pyproject.toml          # Конфигурация Poetry
├── poetry.lock             # Фиксация версий
└── README.md               # Документация
```

## Архитектура

```
Request → Route → Service → Repository → Database
              ↓         ↓
           Schema    Model
```

- **Route** — валидация запроса, HTTP статусы
- **Service** — бизнес-логика (хеширование, блокировка)
- **Repository** — операции с БД (CRUD, блокировка через FOR UPDATE)

## Healthchecks

- `/health` — проверка подключения к БД (для Kubernetes)
- `/live` — liveness probe (всегда alive)
- `/ready` — readiness probe (проверяет БД)

## Требования

- Python 3.12+
- Poetry
- Docker (опционально)
- PostgreSQL 14+ (для локального запуска)

## Лицензия

MIT

## Автор

Нияз (cashap.niyaz20@gmail.com)
```