# repositories/users.py
from typing import Sequence, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from models import User
from config import _LOCK_ONE_USER_SQL
from datetime import datetime, timedelta

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_all(self) -> Sequence[User]:
        result = await self.db.execute(select(User).order_by(User.created_at))
        return result.scalars().all()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def lock_available_user(self, now: datetime, lock_minutes: int) -> Optional[UUID]:
        new_lock = now + timedelta(minutes=lock_minutes)
        result = await self.db.execute(
            _LOCK_ONE_USER_SQL, {"now": now, "new_lock": new_lock}
        )
        row = result.fetchone()
        await self.db.commit()
        return row[0] if row else None 

    async def unlock_all(self) -> int:
        result = await self.db.execute(update(User).values(locktime=None))
        await self.db.commit()
        return result.rowcount

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()