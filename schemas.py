from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from typing import Literal

Env = Literal["prod", "stage", "preriod"]
Domain = Literal["canary", "regular"]

class BaseUser(BaseModel):
    login: EmailStr
    project_id: UUID
    env: Env
    domain: Domain

class UserCreate(BaseUser):
    password: str
    

class UserResponse(BaseUser):
    id: UUID
    created_at: datetime
    locktime: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
