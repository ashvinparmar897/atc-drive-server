from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.folder import FolderCreate, FolderOut, FolderUpdate
from app.crud.folder import create_folder, get_folder, get_folders, update_folder, delete_folder
from app.crud.user import is_admin, can_edit, can_view
from app.api.deps import get_db, get_current_active_user
from app.models.folder import Folder
from app.models.user import RoleEnum
from typing import List

router = APIRouter(prefix="/api/folders", tags=["folders"])

@router.post("/", response_model=FolderOut)
def create_folder_api(folder: FolderCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    # Check permissions
    if folder.parent_id:
        parent_folder = get_folder(db, folder.parent_id)
        if not parent_folder:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        
        # For depth > 1, check if user can edit in parent folder
        if parent_folder.parent_id is not None:
            # Depth > 1 - no access control needed, just check if user can edit
            if not can_edit(current_user):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        else:
            # Depth 1 - check access control
            if parent_folder.access_control:
                user_role = parent_folder.access_control.get(str(current_user.id))
                if not user_role or user_role not in [RoleEnum.admin, RoleEnum.editor]:
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
            elif not can_edit(current_user):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        # Root folder - only admins can create
        if not is_admin(current_user):
            raise HTTPException(status_code=403, detail="Only admins can create root folders")
    
    return create_folder(db, folder, current_user.id)

@router.get("/", response_model=List[FolderOut])
def list_folders(parent_id: int = None, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    folders = get_folders(db, parent_id=parent_id)
    
    # Filter based on permissions
    accessible_folders = []
    for folder in folders:
        if folder.parent_id is None:
            # Root folders - check if user has access
            if folder.access_control:
                user_role = folder.access_control.get(str(current_user.id))
                if user_role in [RoleEnum.admin, RoleEnum.editor, RoleEnum.viewer]:
                    accessible_folders.append(folder)
            elif is_admin(current_user):
                accessible_folders.append(folder)
        else:
            # Sub-folders - no access control needed
            accessible_folders.append(folder)
    
    return accessible_folders

@router.get("/{folder_id}", response_model=FolderOut)
def get_folder_api(folder_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check permissions
    if folder.parent_id is None and folder.access_control:
        user_role = folder.access_control.get(str(current_user.id))
        if not user_role or user_role not in [RoleEnum.admin, RoleEnum.editor, RoleEnum.viewer]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif not can_view(current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return folder

@router.put("/{folder_id}", response_model=FolderOut)
def update_folder_api(folder_id: int, folder_update: FolderUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check permissions
    if folder.parent_id is None and folder.access_control:
        user_role = folder.access_control.get(str(current_user.id))
        if not user_role or user_role not in [RoleEnum.admin, RoleEnum.editor]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif not can_edit(current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_folder(db, folder_id, folder_update)

@router.delete("/{folder_id}")
def delete_folder_api(folder_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check permissions
    if folder.parent_id is None and folder.access_control:
        user_role = folder.access_control.get(str(current_user.id))
        if not user_role or user_role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Only admins can delete folders")
    elif not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can delete folders")
    
    delete_folder(db, folder_id)
    return {"msg": "Folder deleted successfully"}

@router.post("/{folder_id}/access")
def update_folder_access(folder_id: int, access_control: dict, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Only root folders can have access control
    if folder.parent_id is not None:
        raise HTTPException(status_code=400, detail="Access control can only be set on root folders")
    
    # Only admins can set access control
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Only admins can set access control")
    
    folder.access_control = access_control
    db.commit()
    db.refresh(folder)
    
    return {"msg": "Access control updated successfully"} 