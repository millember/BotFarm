# services/users.py
from uuid import UUID
from typing import Sequence
from datetime import datetime
from repositories.users import UserRepository
from models import User
from schemas import UserCreate
from auth import hash_password
from config import MOSCOW_TZ, LOCK_DURATION_MINUTES

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        existing = await self.repo.get_by_login(user_data.login)
        if existing:
            raise ValueError("User with this login already exists")

        now = datetime.now(MOSCOW_TZ)
        new_user = User(
            login=user_data.login,
            password=hash_password(user_data.password),
            project_id=user_data.project_id,
            env=user_data.env,
            domain=user_data.domain,
            created_at=now,
            locktime=None
        )
        return await self.repo.create(new_user)

    async def get_users(self) -> Sequence[User]:
        return await self.repo.get_all()

    async def lock_user(self) -> User:
        now = datetime.now(MOSCOW_TZ)
        user_id = await self.repo.lock_available_user(now, LOCK_DURATION_MINUTES)
        if not user_id:
            raise ValueError("No free users available")  # <-- Это будет поймано в роутере
        
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise RuntimeError("User disappeared after lock")
        return user

    async def unlock_users(self) -> int:
        return await self.repo.unlock_all()

    async def delete_user(self, user_id: UUID) -> bool:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        return True