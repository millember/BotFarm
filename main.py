# main.py
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_database, init_database
from schemas import UserCreate, UserResponse
from services.users import (
    create_user as create_user_service,
    get_users as get_users_service,
    lock_user as lock_user_service,
    unlock_users as unlock_users_service,
    delete_user as delete_user_service,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    print("База данных готова")
    yield
    print("Завершение работы")


botfarm = FastAPI(lifespan=lifespan)


@botfarm.get("/")
def hello():
    return {"message": "Hello, BotFarm!"}


@botfarm.get("/health")
async def health(database: AsyncSession = Depends(get_database)):
    try:
        await database.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "service": "botfarm"}


@botfarm.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, database: AsyncSession = Depends(get_database)):
    try:
        return await create_user_service(database, user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@botfarm.get("/users", response_model=list[UserResponse])
async def get_users(database: AsyncSession = Depends(get_database)):
    return await get_users_service(database)


@botfarm.post("/users/lock", response_model=UserResponse)
async def lock_user(database: AsyncSession = Depends(get_database)):
    try:
        return await lock_user_service(database)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@botfarm.post("/users/unlock")
async def unlock_users(database: AsyncSession = Depends(get_database)):
    count = await unlock_users_service(database)
    return {"message": f"Unlocked {count} users"}


@botfarm.delete("/users/{user_id}")
async def delete_user(user_id: UUID, database: AsyncSession = Depends(get_database)):
    deleted = await delete_user_service(database, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deleted"}