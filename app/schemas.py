from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    class Config:
        orm_mode = True

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderCreate(FolderBase):
    pass

class FolderOut(FolderBase):
    id: int
    owner_id: int
    access_control: Optional[Dict[str, RoleEnum]]
    class Config:
        orm_mode = True

class FileBase(BaseModel):
    filename: str
    folder_id: int

class FileCreate(FileBase):
    pass

class FileOut(FileBase):
    id: int
    s3_key: str
    uploaded_by: int
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 