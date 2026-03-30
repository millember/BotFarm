# main.py
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from schemas import UserCreate, UserResponse
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from database import get_database, init_database
from models import User
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from auth import hash_password
from sqlalchemy.exc import IntegrityError

LOCK_DURATION_MINUTES = 30

# Определяем московский часовой пояс
MOSCOW_TZ = timezone(timedelta(hours=3))


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    """Управление жизненным циклом приложения"""
    await init_database()
    print("База данных готова")
    yield
    print("Завершение работы")


botfarm = FastAPI(lifespan=lifespan)


@botfarm.get("/")
def hello():
    return {"message": "Hello, BotFarm!"}


@botfarm.get("/health")
def health():
    return {"status": "ok", "service": "botfarm"}


@botfarm.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, database: AsyncSession = Depends(get_database)):
    # Используем московское время
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
        raise HTTPException(
            status_code=409, detail="User with this login already exists"
        )
    await database.refresh(database_user)
    return database_user


@botfarm.get("/users", response_model=list[UserResponse])
async def get_users(database: AsyncSession = Depends(get_database)):
    results = await database.execute(select(User).order_by(User.created_at))
    users = results.scalars().all()
    return users


@botfarm.post("/users/lock", response_model=UserResponse)
async def lock_user(database: AsyncSession = Depends(get_database)):
    # Используем московское время
    now_moscow = datetime.now(MOSCOW_TZ)

    condition = (User.locktime == None) | (User.locktime < now_moscow)
    results = await database.execute(
        select(User).where(condition).order_by(User.created_at).limit(1)
    )
    user = results.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="No free users available")

    user.locktime = now_moscow + timedelta(minutes=30)
    await database.commit()
    await database.refresh(user)
    return user


@botfarm.post("/users/unlock")
async def unlock_users(database: AsyncSession = Depends(get_database)):
    results = await database.execute(update(User).values(locktime=None))
    await database.commit()
    count = results.rowcount
    return {"message": f"Unlocked {count} users"}


@botfarm.delete("/users/{user_id}")
async def delete_user(user_id: str, database: AsyncSession = Depends(get_database)):
    result = await database.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await database.delete(user)
    await database.commit()
    return {"message": f"User {user_id} deleted"}
