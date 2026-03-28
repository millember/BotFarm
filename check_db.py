import asyncio
from sqlalchemy import text
from database import engine

async def check_connection():
    """Проверяет подключение к базе данных"""
    print("Проверяем подключение к PostgreSQL")
    print("URL: postgresql+asyncpg://oppennec@localhost:5432/botfarm")

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            value = result.scalar()
            print("ПОДКЛЮЧЕНИЕ РАБОТАЕТ!")
            print("Результат запроса: {value}")
            return True
    except Exception as e:
        print("ОШИБКА ПОДКЛЮЧЕНИЯ:")
        print("{e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_connection())