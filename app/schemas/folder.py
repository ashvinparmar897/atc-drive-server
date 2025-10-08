from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.user import RoleEnum

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    name: Optional[str] = None

class FolderOut(FolderBase):
    id: int
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FolderAccessUpdate(BaseModel):
    user_id: int
    role: RoleEnum 