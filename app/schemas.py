from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    login: EmailStr
    password: str
    project_id: UUID
    env: str
    domain: str


class UserResponse(UserCreate):
    id: UUID
    created_at: datetime
    locktime: Optional[datetime] = None
