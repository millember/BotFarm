# main.py
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_database, init_database
from routes.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    print("База данных готова")
    yield
    print("Завершение работы")

botfarm = FastAPI(lifespan=lifespan)

botfarm.include_router(users_router)

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

@botfarm.get("/live")
def liveness():
    return {"status": "alive"}

@botfarm.get("/ready")
async def readiness(database: AsyncSession = Depends(get_database)):
    try:
        await database.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")