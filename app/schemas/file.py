from pydantic import BaseModel
from typing import Optional

class FileBase(BaseModel):
    filename: str
    folder_id: int

class FileCreate(FileBase):
    pass

class FileUpdate(BaseModel):
    filename: Optional[str] = None
    folder_id: Optional[int] = None

class FileMove(BaseModel):
    new_folder_id: int

class FileOut(FileBase):
    id: int
    s3_key: Optional[str] = None
    uploaded_by: int
    storage_type: Optional[str] = None
    storage_key: Optional[str] = None
    
    class Config:
        from_attributes = True 