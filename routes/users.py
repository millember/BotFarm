from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_database
from repositories.users import UserRepository
from services.users import UserService
from schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service(db: AsyncSession = Depends(get_database)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

@router.post("", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    try:
        return await service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("", response_model=list[UserResponse])
async def get_users(service: UserService = Depends(get_user_service)):
    return await service.get_users()

@router.post("/lock", response_model=UserResponse)
async def lock_user(service: UserService = Depends(get_user_service)):
    try:
        return await service.lock_user()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/unlock")
async def unlock_users(service: UserService = Depends(get_user_service)):
    count = await service.unlock_users()
    return {"message": f"Unlocked {count} users"}

@router.delete("/{user_id}")
async def delete_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deleted"}