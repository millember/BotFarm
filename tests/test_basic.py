# tests/test_basic.py
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import text


class TestBotFarmBasic:

    async def test_block_and_release_user(self, client: AsyncClient):
        """
        Тест проверяет блокировку и разблокировку пользователя:
        1. Создает нового пользователя
        2. Блокирует его (устанавливает locktime)
        3. Проверяет, что пользователь заблокирован
        4. Разблокирует всех пользователей
        5. Проверяет, что блокировка снята
        """
        user_data = {
            "login": "locktest@example.com",
            "password": "Password123!",
            "project_id": str(uuid4()),
            "env": "prod",
            "domain": "canary",
        }

        create_response = await client.post("/users", json=user_data)
        assert create_response.status_code == 201
        created_user = create_response.json()
        assert created_user["locktime"] is None

        lock_response = await client.post("/users/lock")
        assert lock_response.status_code == 200

        locked_user = lock_response.json()
        assert locked_user["locktime"] is not None
        assert locked_user["login"] == user_data["login"]

        get_response = await client.get("/users")
        users = get_response.json()

        for user in users:
            if user["login"] == user_data["login"]:
                assert user["locktime"] is not None
                break

        unlock_response = await client.post("/users/unlock")
        assert unlock_response.status_code == 200
        assert "Unlocked" in unlock_response.json()["message"]

        get_response2 = await client.get("/users")
        users2 = get_response2.json()

        for user in users2:
            if user["login"] == user_data["login"]:
                assert user["locktime"] is None
                break

    async def test_remove_user(self, client: AsyncClient):
        """
        Тест проверяет удаление пользователя:
        1. Создает нового пользователя
        2. Проверяет, что он есть в списке
        3. Удаляет пользователя по ID
        4. Проверяет, что пользователь удален из списка
        5. Проверяет ошибку при удалении несуществующего пользователя
        """
        user_data = {
            "login": "deletetest@example.com",
            "password": "DeletePass123!",
            "project_id": str(uuid4()),
            "env": "stage",
            "domain": "regular",
        }

        create_response = await client.post("/users", json=user_data)
        assert create_response.status_code == 201
        created_user = create_response.json()
        user_id = created_user["id"]

        get_before = await client.get("/users")
        users_before = get_before.json()
        assert any(u["id"] == user_id for u in users_before)

        delete_response = await client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 200
        assert f"User {user_id} deleted" in delete_response.json()["message"]

        get_after = await client.get("/users")
        users_after = get_after.json()
        assert not any(u["id"] == user_id for u in users_after)

        fake_id = str(uuid4())
        delete_fake = await client.delete(f"/users/{fake_id}")
        assert delete_fake.status_code == 404
        assert "User not found" in delete_fake.json()["detail"]

    async def test_service_health_checks(self, client: AsyncClient):
        """
        Тест проверяет работоспособность сервиса:
        1. Проверяет корневой эндпоинт (/)
        2. Проверяет эндпоинт здоровья (/health)
        """
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello, BotFarm!"

        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "botfarm"

    async def test_password_hashing(self, client: AsyncClient):
        """
        Тест проверяет хеширование паролей:
        1. Хеширует пароль
        2. Проверяет, что правильный пароль проходит верификацию
        3. Проверяет, что неправильный пароль не проходит верификацию
        """
        from auth import hash_password, verify_password

        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    async def test_database_initialization(self, client: AsyncClient):
        """
        Тест проверяет инициализацию базы данных:
        1. Вызывает инициализацию БД
        2. Проверяет, что можно выполнить запрос к таблице users
        """
        from database import init_database, engine

        await init_database()

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT * FROM users LIMIT 1"))
            assert result is not None
