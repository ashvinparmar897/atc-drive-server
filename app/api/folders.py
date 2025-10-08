from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.folder import FolderCreate, FolderOut, FolderUpdate
from app.crud.folder import create_folder, get_folder, get_folders, update_folder, delete_folder
from app.crud.user import is_admin, can_edit
from app.api.deps import get_db, get_current_active_user
from app.models.folder import Folder
from app.models.folder_permissions import FolderPermission
from app.models.user import RoleEnum, User
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/folders", tags=["folders"])

class FolderPermissionRequest(BaseModel):
    user_email: str
    action: str  # "add" or "remove"
    permission: Optional[str] = None  # Optional for remove action

@router.post("/", response_model=FolderOut)
def create_folder_api(folder: FolderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not can_edit(current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if folder.parent_id:
        parent_folder = get_folder(db, folder.parent_id)
        if not parent_folder:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        
        permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == folder.parent_id,
            FolderPermission.user_id == current_user.id,
            FolderPermission.permission == RoleEnum.editor
        ).first()
        if not permission and not is_admin(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions to create in this folder")
    
    new_folder = create_folder(db, folder, current_user.id)
    
    if current_user.role in [RoleEnum.editor, RoleEnum.admin]:
        existing_permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == new_folder.id,
            FolderPermission.user_id == current_user.id
        ).first()
        if not existing_permission:
            folder_permission = FolderPermission(
                folder_id=new_folder.id,
                user_id=current_user.id,
                permission=RoleEnum.editor
            )
            db.add(folder_permission)
            db.commit()
    
    return new_folder

@router.get("/", response_model=List[FolderOut])
def list_folders(parent_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if parent_id in ["", "null", "undefined"]:
        parent_id = None
    elif parent_id is not None:
        try:
            parent_id = int(parent_id)
        except ValueError:
            parent_id = None
    
    query = db.query(Folder)
    if parent_id is not None:
        query = query.filter(Folder.parent_id == parent_id)
    else:
        query = query.filter(Folder.parent_id.is_(None))
    
    if not is_admin(current_user):
        query = query.join(FolderPermission, Folder.id == FolderPermission.folder_id, isouter=True).filter(
            FolderPermission.user_id == current_user.id
        )
    
    folders = query.all()
    return folders

@router.get("/{folder_id}", response_model=FolderOut)
def get_folder_api(folder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if not is_admin(current_user):
        permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == folder_id,
            FolderPermission.user_id == current_user.id
        ).first()
        if not permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return folder

@router.put("/{folder_id}", response_model=FolderOut)
def update_folder_api(folder_id: int, folder_update: FolderUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if not is_admin(current_user):
        permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == folder_id,
            FolderPermission.user_id == current_user.id,
            FolderPermission.permission == RoleEnum.editor
        ).first()
        if not permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_folder(db, folder_id, folder_update)

@router.delete("/{folder_id}")
def delete_folder_api(folder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete folders")
    
    delete_folder(db, folder_id)
    return {"msg": "Folder deleted successfully"}

@router.get("/{folder_id}/permissions", response_model=List[str])
def get_folder_permissions(folder_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can view permissions")
    
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    permissions = db.query(FolderPermission).filter(FolderPermission.folder_id == folder_id).all()
    return [perm.user.email for perm in permissions]

@router.post("/{folder_id}/permissions")
def manage_folder_permission(
    folder_id: int,
    permission: FolderPermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can manage permissions")
    
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    user_email = permission.user_email
    action = permission.action
    permission_type = permission.permission
    
    if action not in ["add", "remove"]:
        raise HTTPException(status_code=400, detail="Invalid action: must be 'add' or 'remove'")
    
    if action == "add" and permission_type not in ["editor", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid permission: must be 'editor' or 'viewer'")
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action == "add":
        existing_permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == folder_id,
            FolderPermission.user_id == user.id
        ).first()
        if existing_permission:
            raise HTTPException(status_code=400, detail="Permission already exists")
        
        new_permission = FolderPermission(
            folder_id=folder_id,
            user_id=user.id,
            permission=permission_type
        )
        db.add(new_permission)
        db.commit()
        return {"msg": "Permission added successfully"}
    else:
        permission = db.query(FolderPermission).filter(
            FolderPermission.folder_id == folder_id,
            FolderPermission.user_id == user.id
        ).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        db.delete(permission)
        db.commit()
        return {"msg": "Permission removed successfully"}

@router.get("/users/{user_email}/folder_permissions", response_model=List[FolderOut])
def get_user_folder_permissions(user_email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can view user permissions")
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    folders = db.query(Folder).join(FolderPermission).filter(FolderPermission.user_id == user.id).all()
    return folders