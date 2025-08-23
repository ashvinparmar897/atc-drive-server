from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, crud, auth, database
from typing import List

router = APIRouter(prefix="/folders", tags=["folders"])

@router.post("/", response_model=schemas.FolderOut)
def create_folder(folder: schemas.FolderCreate, db: Session = Depends(database.SessionLocal), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.create_folder(db, folder, owner_id=current_user.id)

@router.get("/", response_model=List[schemas.FolderOut])
def list_folders(db: Session = Depends(database.SessionLocal), current_user: models.User = Depends(auth.get_current_active_user)):
    return db.query(models.Folder).filter((models.Folder.owner_id == current_user.id) | (models.Folder.access_control != None)).all()

@router.patch("/{folder_id}/access")
def update_access_control(folder_id: int, access_control: dict, db: Session = Depends(database.SessionLocal), current_user: models.User = Depends(auth.get_current_active_user)):
    folder = crud.get_folder(db, folder_id)
    if not folder or folder.parent_id is not None:
        raise HTTPException(status_code=404, detail="Folder not found or not a depth 1 folder")
    if folder.owner_id != current_user.id and current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    folder.access_control = access_control
    db.commit()
    return {"msg": "Access control updated"} 