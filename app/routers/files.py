from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, crud, auth, database, s3_utils
from typing import List

ALLOWED_EXTENSIONS = {"png", "svg", "pdf", "ai", "cdr", "stp", "dwg", "x_t"}  # x_t = parasolid
MAX_FILE_SIZE_MB = 100
MAX_FILES = 100

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=List[schemas.FileOut])
async def upload_files(folder_id: int, files: List[UploadFile] = File(...), db: Session = Depends(database.SessionLocal), current_user: models.User = Depends(auth.get_current_active_user)):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail="Too many files (max 100)")
    folder = crud.get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    # Access control check (depth 1 only)
    if folder.parent_id is None and folder.access_control:
        role = folder.access_control.get(str(current_user.id)) or current_user.role
        if role not in [models.RoleEnum.admin, models.RoleEnum.editor]:
            raise HTTPException(status_code=403, detail="No upload permission")
    uploaded = []
    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
        size = 0
        async for chunk in file:
            size += len(chunk)
            if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large")
        await file.seek(0)
        s3_key = await s3_utils.upload_file_to_s3(file, folder=str(folder_id))
        db_file = crud.create_file(db, schemas.FileCreate(filename=file.filename, folder_id=folder_id), s3_key, current_user.id)
        uploaded.append(db_file)
    return uploaded

@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(database.SessionLocal), current_user: models.User = Depends(auth.get_current_active_user)):
    file = crud.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    folder = crud.get_folder(db, file.folder_id)
    # Access control check (depth 1 only)
    if folder.parent_id is None and folder.access_control:
        role = folder.access_control.get(str(current_user.id)) or current_user.role
        if role not in [models.RoleEnum.admin, models.RoleEnum.editor, models.RoleEnum.viewer]:
            raise HTTPException(status_code=403, detail="No download permission")
    url = s3_utils.get_s3_download_url(file.s3_key)
    return {"url": url} 