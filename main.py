from fastapi import FastAPI
from schemas import UserCreate,UserResponse
from uuid import uuid4
from datetime import datetime, timedelta

LOCK_DURATION_MINUTES = 30

botfarm = FastAPI()
user_datebase = []

@botfarm.get("/")
def hello():
    return {"message": "Hello, BotFarm!"}

@botfarm.get("/health")
def health():
    return {"status":"ok", "service":"botfarm"}

@botfarm.post("/users", response_model=UserResponse,status_code=201)
def create_user(user: UserCreate):
    new_user = {
        "id": uuid4(),
        "created_at": datetime.utcnow() + timedelta(hours=3),
        "login": user.login,
        "password": user.password,
        "project_id": user.project_id,
        "env": user.env,
        "domain": user.domain,
        "locktime":None
    }
    user_datebase.append(new_user)
    return new_user

@botfarm.get("/users", response_model=list[UserResponse])
def get_users():
    return user_datebase

@botfarm.post("/users/lock")
def lock_user():
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    
    for user in user_datebase:
        if user["locktime"] is None or user["locktime"]< now_moscow:
            user["locktime"] = now_moscow+timedelta(minutes=LOCK_DURATION_MINUTES)
            return user
    
    return {"error": "No free users available"}

@botfarm.post("/users/unlock")
def unlock_users():
    for user in user_datebase:
        user["locktime"] = None
    return {"message": f"Unlocked {len(user_datebase)} users"}