# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from main import botfarm
from database import Base, get_database

# Тестовая база данных
TEST_DATABASE_URL = "postgresql+asyncpg://oppennec@localhost:5432/botfarm_test"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

AsyncSessionLocalTest = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


async def override_get_database() -> AsyncGenerator[AsyncSession, None]:
    """Переопределение зависимости для тестов"""
    async with AsyncSessionLocalTest() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестовой сессии"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Создание и очистка таблиц перед каждым тестом"""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для тестового клиента FastAPI"""
    botfarm.dependency_overrides[get_database] = override_get_database

    transport = ASGITransport(app=botfarm)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    botfarm.dependency_overrides.clear()
