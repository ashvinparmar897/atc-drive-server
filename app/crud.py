from sqlalchemy.orm import Session
from . import models, schemas, auth
from typing import Optional

# User CRUD

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Folder CRUD

def create_folder(db: Session, folder: schemas.FolderCreate, owner_id: int):
    db_folder = models.Folder(
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=owner_id,
        access_control={} if folder.parent_id is None else None
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder

def get_folder(db: Session, folder_id: int):
    return db.query(models.Folder).filter(models.Folder.id == folder_id).first()

# File CRUD

def create_file(db: Session, file: schemas.FileCreate, s3_key: str, uploaded_by: int):
    db_file = models.File(
        filename=file.filename,
        folder_id=file.folder_id,
        s3_key=s3_key,
        uploaded_by=uploaded_by
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first() 