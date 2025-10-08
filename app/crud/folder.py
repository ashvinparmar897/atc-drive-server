from sqlalchemy.orm import Session
from app.models.folder import Folder
from app.models.folder_permissions import FolderPermission
from app.schemas.folder import FolderCreate, FolderUpdate
from app.models.user import RoleEnum
from typing import List, Optional

def create_folder(db: Session, folder: FolderCreate, owner_id: int) -> Folder:
    db_folder = Folder(
        name=folder.name,
        parent_id=folder.parent_id,
        owner_id=owner_id
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder

def get_folder(db: Session, folder_id: int) -> Optional[Folder]:
    return db.query(Folder).filter(Folder.id == folder_id).first()

def get_folders(db: Session, parent_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Folder]:
    query = db.query(Folder)
    if parent_id is not None:
        query = query.filter(Folder.parent_id == parent_id)
    else:
        query = query.filter(Folder.parent_id.is_(None))
    return query.offset(skip).limit(limit).all()

def update_folder(db: Session, folder_id: int, folder_update: FolderUpdate) -> Optional[Folder]:
    db_folder = get_folder(db, folder_id)
    if not db_folder:
        return None
    
    update_data = folder_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_folder, field, value)
    
    db.commit()
    db.refresh(db_folder)
    return db_folder

def delete_folder(db: Session, folder_id: int) -> bool:
    db_folder = get_folder(db, folder_id)
    if not db_folder:
        return False
    
    from app.models.file import File
    has_files = db.query(File).filter(File.folder_id == folder_id).count() > 0
    has_subfolders = db.query(Folder).filter(Folder.parent_id == folder_id).count() > 0
    
    if has_files or has_subfolders:
        raise ValueError("Cannot delete folder with files or subfolders")
    
    db.delete(db_folder)
    db.commit()
    return True

def get_folder_path(db: Session, folder_id: int) -> List[Folder]:
    path = []
    current_folder = get_folder(db, folder_id)
    
    while current_folder:
        path.insert(0, current_folder)
        if current_folder.parent_id:
            current_folder = get_folder(db, current_folder.parent_id)
        else:
            break
    
    return path

def get_user_accessible_folders(db: Session, user_id: int, user_role: str) -> List[Folder]:
    if user_role == "admin":
        return db.query(Folder).all()
    
    return db.query(Folder).join(FolderPermission).filter(FolderPermission.user_id == user_id).all()