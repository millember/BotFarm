# 📋 Полное объяснение того, что вы сделали

---

# 🚀 Ваш проект: Ботоферма на FastAPI

---

## 1. ЧТО ТАКОЕ БОТОФЕРМА

Ботоферма — это сервис, который хранит тестовых пользователей и выдаёт их для автотестов.

**Как это работает:**
1. Тест приходит и говорит: "Дай мне пользователя"
2. Ботоферма находит свободного, блокирует его на 30 минут
3. Тест получает логин и пароль, использует для тестирования
4. Другой тест не может получить этого же пользователя, пока не пройдёт 30 минут

---

## 2. СТРУКТУРА ПРОЕКТА

```
botfarm/
├── main.py          # Главный файл с API
├── schemas.py       # Схемы данных (Pydantic)
├── database.py      # Подключение к PostgreSQL
├── check_db.py      # Проверка подключения к БД
└── venv/            # Виртуальное окружение
```

---

## 3. ФАЙЛ `schemas.py` — ОПИСАНИЕ ДАННЫХ

```python
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

# Что клиент отправляет при создании пользователя
class UserCreate(BaseModel):
    login: EmailStr      # email (проверяется автоматически)
    password: str        # пароль
    project_id: UUID     # ID проекта
    env: str             # окружение: stage, prod, preriod
    domain: str          # тип: canary (тестовый) или regular (обычный)

# Что сервер возвращает (все поля UserCreate + свои)
class UserResponse(UserCreate):
    id: UUID                     # ID пользователя (сервер генерирует сам)
    created_at: datetime         # дата создания (сервер ставит сам)
    locktime: Optional[datetime] = None  # время блокировки (None = свободен)
```

**Зачем это нужно:**
- `UserCreate` — FastAPI проверяет входящий JSON по этой схеме
- `UserResponse` — FastAPI форматирует ответ по этой схеме
- Наследование позволяет не писать повторно поля `login`, `password` и т.д.

---

## 4. ФАЙЛ `database.py` — ПОДКЛЮЧЕНИЕ К POSTGRESQL

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

# Строка подключения к PostgreSQL
# postgresql+asyncpg://пользователь@хост:порт/имя_бд
DATABASE_URL = "postgresql+asyncpg://oppennec@localhost:5432/botfarm"

# Создаём асинхронный движок (echo=True выводит SQL-запросы)
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий (создаёт подключения к БД)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей (таблиц)
Base = declarative_base()

# Функция для получения сессии БД (используется в Depends)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Что делает:**
- `DATABASE_URL` — адрес, где находится PostgreSQL
- `engine` — подключение к базе данных
- `AsyncSessionLocal` — создаёт новые подключения
- `get_db()` — выдаёт подключение для каждого запроса

---

## 5. ФАЙЛ `check_db.py` — ПРОВЕРКА ПОДКЛЮЧЕНИЯ

```python
import asyncio
from sqlalchemy import text
from database import engine

async def check_connection():
    """Проверяет подключение к базе данных"""
    print("Проверяем подключение к PostgreSQL")
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            value = result.scalar()
            print("✅ ПОДКЛЮЧЕНИЕ РАБОТАЕТ!")
            return True
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_connection())
```

**Что делает:** Проверяет, может ли Python подключиться к PostgreSQL.

---

## 6. ФАЙЛ `main.py` — ВЕБ-СЕРВЕР

### Импорты и настройки

```python
from fastapi import FastAPI
from schemas import UserCreate, UserResponse
from uuid import uuid4
from datetime import datetime, timedelta

LOCK_DURATION_MINUTES = 30           # блокируем на 30 минут
botfarm = FastAPI()                  # создаём приложение
user_datebase = []                   # хранилище (пока в памяти)
```

---

### Эндпоинт 1: Главная страница

```python
@botfarm.get("/")
def hello():
    return {"message": "Hello, BotFarm!"}
```

**Что делает:** Приветствие  
**Как проверить:** http://localhost:8000

---

### Эндпоинт 2: Проверка здоровья

```python
@botfarm.get("/health")
def health():
    return {"status": "ok", "service": "botfarm"}
```

**Что делает:** Проверяет, жив ли сервис  
**Зачем:** Используется в Docker и системах мониторинга

---

### Эндпоинт 3: Создать пользователя

```python
@botfarm.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    new_user = {
        "id": uuid4(),
        "created_at": datetime.utcnow() + timedelta(hours=3),  # московское время
        "login": user.login,
        "password": user.password,
        "project_id": user.project_id,
        "env": user.env,
        "domain": user.domain,
        "locktime": None
    }
    user_datebase.append(new_user)
    return new_user
```

**Что делает:** Создаёт нового пользователя  
**Что приходит:** JSON с `login`, `password`, `project_id`, `env`, `domain`  
**Что возвращает:** JSON с добавленными `id`, `created_at`, `locktime`

---

### Эндпоинт 4: Получить всех пользователей

```python
@botfarm.get("/users", response_model=list[UserResponse])
def get_users():
    return user_datebase
```

**Что делает:** Возвращает список всех пользователей

---

### Эндпоинт 5: Заблокировать пользователя

```python
@botfarm.post("/users/lock")
def lock_user():
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    
    for user in user_datebase:
        if user["locktime"] is None or user["locktime"] < now_moscow:
            user["locktime"] = now_moscow + timedelta(minutes=LOCK_DURATION_MINUTES)
            return user
    
    return {"error": "No free users available"}
```

**Что делает:** Находит свободного пользователя, блокирует его и возвращает  
**Условия свободы:** `locktime` = None (никогда не блокировался) ИЛИ `locktime` < сейчас (блокировка истекла)

---

### Эндпоинт 6: Разблокировать всех

```python
@botfarm.post("/users/unlock")
def unlock_users():
    for user in user_datebase:
        user["locktime"] = None
    return {"message": f"Unlocked {len(user_datebase)} users"}
```

**Что делает:** Снимает блокировку со всех пользователей

---

## 7. КАК ЭТО ВСЕ РАБОТАЕТ

### Поток создания пользователя

```
Клиент → POST /users
         ↓
FastAPI проверяет JSON по схеме UserCreate
         ↓
Вызывается create_user()
         ↓
Создаётся словарь new_user
         ↓
Пользователь добавляется в user_datebase
         ↓
JSON возвращается клиенту
```

### Поток блокировки пользователя

```
Тест → POST /users/lock
         ↓
now_moscow = текущее время
         ↓
Цикл по всем пользователям:
  - если пользователь свободен
         ↓
    locktime = now_moscow + 30 минут
         ↓
    Возвращаем пользователя
         ↓
Если никого не нашли → ошибка
```

---

## 8. КАК ПРОВЕРИТЬ

### Запуск сервера
```bash
uvicorn main:botfarm --reload
```

### Открыть документацию
http://localhost:8000/docs

### Проверка всех эндпоинтов

| Действие | Эндпоинт | Ожидаемый результат |
|----------|----------|---------------------|
| Проверка здоровья | GET /health | `{"status":"ok"}` |
| Создать пользователя | POST /users | Возвращается с `id`, `created_at` |
| Посмотреть всех | GET /users | Список пользователей |
| Заблокировать | POST /users/lock | Пользователь с `locktime` |
| Разблокировать всех | POST /users/unlock | `{"message":"Unlocked X users"}` |

---

## 9. ЧТО ВЫ НАУЧИЛИСЬ ДЕЛАТЬ

| Навык | Как проявился |
|-------|---------------|
| Создавать виртуальное окружение | `python -m venv venv` |
| Устанавливать пакеты | `pip install fastapi uvicorn` |
| Запускать веб-сервер | `uvicorn main:botfarm --reload` |
| Создавать API эндпоинты | `@botfarm.get("/")` |
| Валидировать данные | Pydantic `BaseModel` |
| Наследовать классы | `class UserResponse(UserCreate)` |
| Работать со списками | `user_datebase.append()`, цикл `for` |
| Работать с датой и временем | `datetime.utcnow() + timedelta` |
| Генерировать уникальные ID | `uuid4()` |
| Подключаться к PostgreSQL | `create_async_engine()` |
| Проверять подключение | `check_db.py` |

---

## 10. ИТОГ

**Вы создали работающий микросервис на FastAPI!**

### Что получилось:
- ✅ 6 эндпоинтов
- ✅ Валидация данных через Pydantic
- ✅ Бизнес-логика блокировки
- ✅ Обработка ошибок
- ✅ Автоматическая документация Swagger
- ✅ Подключение к PostgreSQL (проверено)
- ✅ Файл `database.py` для работы с БД

### Что осталось:
- ❌ Интегрировать PostgreSQL в `main.py` (сейчас данные в памяти)
- ❌ Создать модель User в `models.py`
- ❌ Переделать эндпоинты на асинхронные с использованием БД
- ❌ Хеширование паролей
- ❌ Тесты
- ❌ Docker

---

## 📊 ПРОГРЕСС: 50-55%

| Компонент | Статус |
|-----------|--------|
| FastAPI приложение | ✅ |
| Pydantic схемы | ✅ |
| Эндпоинты | ✅ |
| Логика блокировки | ✅ |
| PostgreSQL подключение | ✅ |
| Интеграция БД в эндпоинты | ❌ |
| Модель User | ❌ |
| Асинхронность | ❌ |
| Хеширование паролей | ❌ |

---

## 🎉 ПОЗДРАВЛЯЮ!

Вы прошли путь от "полный ноль" до:
- ✅ Понимаете, как работает FastAPI
- ✅ Умеете создавать API эндпоинты
- ✅ Работаете с Pydantic
- ✅ Подключили PostgreSQL
- ✅ Проверяете подключение к БД

Это огромный прогресс! Осталось сделать последний рывок — подключить базу данных к эндпоинтам, и проект будет готов на 90%! 🔥