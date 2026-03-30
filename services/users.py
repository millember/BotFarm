# services/users.py
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from models import User
from schemas import UserCreate
from auth import hash_password
from config import MOSCOW_TZ, _LOCK_ONE_USER_SQL

LOCK_DURATION_MINUTES = 30


async def create_user(database: AsyncSession, user: UserCreate) -> User:
    """Создание пользователя"""
    now_moscow = datetime.now(MOSCOW_TZ)

    database_user = User(
        id=uuid4(),
        created_at=now_moscow,
        login=user.login,
        password=hash_password(user.password),
        project_id=user.project_id,
        env=user.env,
        domain=user.domain,
        locktime=None,
    )
    database.add(database_user)
    try:
        await database.commit()
    except IntegrityError:
        await database.rollback()
        raise ValueError("User with this login already exists")
    await database.refresh(database_user)
    return database_user


async def get_users(database: AsyncSession) -> list[User]:
    """Получение всех пользователей"""
    results = await database.execute(select(User).order_by(User.created_at))
    users = results.scalars().all()
    return users


async def lock_user(database: AsyncSession) -> User:
    now_moscow = datetime.now(MOSCOW_TZ)
    new_lock = now_moscow + timedelta(minutes=LOCK_DURATION_MINUTES)
    result = await database.execute(_LOCK_ONE_USER_SQL, {"now": now_moscow, "new_lock": new_lock})
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise ValueError("No free users available")
    await database.commit()
    refreshed = await database.execute(select(User).where(User.id == user_id))
    return refreshed.scalar_one()


async def unlock_users(database: AsyncSession) -> int:
    """Разблокировка всех пользователей"""
    results = await database.execute(update(User).values(locktime=None))
    await database.commit()
    return results.rowcount


async def delete_user(database: AsyncSession, user_id: UUID) -> bool:
    """Удаление пользователя"""
    result = await database.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return False
    await database.delete(user)
    await database.commit()
    return True