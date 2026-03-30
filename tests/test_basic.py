# tests/test_basic.py
from uuid import uuid4
from httpx import AsyncClient


class TestBotFarmBasic:
    @staticmethod
    def _by_login(users: list[dict], login: str) -> dict:
        return next(u for u in users if u["login"] == login)

    async def test_block_and_release_user(self, client: AsyncClient):
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

        users = (await client.get("/users")).json()
        assert self._by_login(users, user_data["login"])["locktime"] is not None

        unlock_response = await client.post("/users/unlock")
        assert unlock_response.status_code == 200
        assert "Unlocked" in unlock_response.json()["message"]

        users2 = (await client.get("/users")).json()
        assert self._by_login(users2, user_data["login"])["locktime"] is None

    async def test_create_user_duplicate_login_returns_409(self, client: AsyncClient):
        user_data = {
            "login": "duplicate@example.com",
            "password": "Password123!",
            "project_id": str(uuid4()),
            "env": "prod",
            "domain": "regular",
        }

        r1 = await client.post("/users", json=user_data)
        assert r1.status_code == 201

        r2 = await client.post("/users", json=user_data)
        assert r2.status_code == 409
        assert "already exists" in r2.json()["detail"]

    async def test_lock_user_when_none_available_returns_404(self, client: AsyncClient):
        r = await client.post("/users/lock")
        assert r.status_code == 404
        assert "No free users" in r.json()["detail"]

    async def test_services_layer_branches(self, client: AsyncClient):
        from services.users import (
            create_user as create_user_service,
            delete_user as delete_user_service,
            get_users as get_users_service,
            lock_user as lock_user_service,
            unlock_users as unlock_users_service,
        )
        from schemas import UserCreate
        import tests.conftest as tc

        async with tc.AsyncSessionLocalTest() as db:
            u = UserCreate(
                login="svc@example.com",
                password="Password123!",
                project_id=uuid4(),
                env="prod",
                domain="regular",
            )
            created = await create_user_service(db, u)
            assert created.login == "svc@example.com"

            try:
                await create_user_service(db, u)
                assert False, "expected ValueError for duplicate login"
            except ValueError as e:
                assert "already exists" in str(e)

            users = await get_users_service(db)
            assert any(x.login == "svc@example.com" for x in users)

        async with tc.AsyncSessionLocalTest() as db2:
            locked = await lock_user_service(db2)
            assert locked.locktime is not None

            try:
                await lock_user_service(db2)
                assert False, "expected ValueError when no free users"
            except ValueError as e:
                assert "No free users available" in str(e)

            unlocked_count = await unlock_users_service(db2)
            assert unlocked_count >= 1

            assert await delete_user_service(db2, uuid4()) is False

            assert await delete_user_service(db2, created.id) is True

    async def test_health_returns_503_when_db_fails(self, client: AsyncClient):
        from main import botfarm
        from database import get_database

        class BrokenSession:
            async def execute(self, *args, **kwargs):
                raise RuntimeError("boom")

        async def override_broken_db():
            yield BrokenSession()

        botfarm.dependency_overrides[get_database] = override_broken_db
        try:
            r = await client.get("/health")
            assert r.status_code == 503
            assert "Database unavailable" in r.json()["detail"]
        finally:
            botfarm.dependency_overrides.pop(get_database, None)

    async def test_remove_user(self, client: AsyncClient):
        user_data = {
            "login": "deletetest@example.com",
            "password": "DeletePass123!",
            "project_id": str(uuid4()),
            "env": "stage",
            "domain": "regular",
        }

        create_response = await client.post("/users", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        users_before = (await client.get("/users")).json()
        assert any(u["id"] == user_id for u in users_before)

        delete_response = await client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 200
        assert f"User {user_id} deleted" in delete_response.json()["message"]

        users_after = (await client.get("/users")).json()
        assert not any(u["id"] == user_id for u in users_after)

        fake_id = str(uuid4())
        delete_fake = await client.delete(f"/users/{fake_id}")
        assert delete_fake.status_code == 404
        assert "User not found" in delete_fake.json()["detail"]

    async def test_service_health_checks(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello, BotFarm!"

        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "botfarm"
