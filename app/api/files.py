from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.file import FileCreate, FileOut, FileUpdate, FileMove
from app.crud.file import create_file, get_file, delete_file, update_file, move_file
from app.api.deps import get_db, get_current_active_user
from app.services.s3 import upload_file_to_s3, get_s3_download_url
from app.services.local_storage import save_file_locally, get_local_file_url, delete_local_file
from app.crud.folder import get_folder
from app.models.user import RoleEnum
from app.models.file import File as FileModel
from app.core.config import settings
from fastapi.responses import FileResponse
import os

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "bmp", "svg", "webp", "ico", "tiff", "tif",
    "pdf", "doc", "docx", "txt", "rtf", "odt", "pages",
    "xls", "xlsx", "csv", "ods", "numbers",
    "ppt", "pptx", "odp", "key",
    "zip", "rar", "7z", "tar", "gz", "bz2",
    "py", "js", "html", "css", "php", "java", "cpp", "c", "cs", "ts", "jsx", "tsx",
    "json", "xml", "yaml", "yml", "md", "sql", "sh", "bat", "ps1",
    "ai", "psd", "cdr", "eps", "indd", "sketch", "fig",
    "dwg", "dxf", "stp", "step", "iges", "x_t", "x_b",
    "mp4", "avi", "mov", "wmv", "flv", "webm", "mkv", "m4v",
    "mp3", "wav", "flac", "aac", "ogg", "wma", "m4a",
    "exe", "msi", "dmg", "pkg", "deb", "rpm", "apk"
}
MAX_FILE_SIZE_MB = 100
MAX_FILES = 100

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/", response_model=List[FileOut])
def list_files(
    folder_id: Optional[str] = Query(None, description="Folder ID or 'root' for root files"),
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    if folder_id == "root" or folder_id is None:
        files = db.query(FileModel).filter(FileModel.folder_id == None).all()
    else:
        files = db.query(FileModel).filter(FileModel.folder_id == int(folder_id)).all()
    return files

@router.post("/upload", response_model=List[FileOut])
async def upload_files(
    folder_id: int, 
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail="Too many files (max 100)")
    
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check permissions for root folder
    if folder.parent_id is None:
        # Assume access_control is a JSON field; fall back to user role if missing
        access_control = getattr(folder, 'access_control', None)
        if access_control:
            role = access_control.get(str(current_user.id)) or current_user.role
        else:
            role = current_user.role
        if role not in [RoleEnum.admin, RoleEnum.editor]:
            raise HTTPException(status_code=403, detail="No upload permission")
    
    uploaded = []
    for file in files:
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        await file.seek(0)
        
        file_path = getattr(file, 'path', '') or file.filename
        if '/' in file_path:
            path_parts = file_path.split('/')
            if len(path_parts) > 1:
                storage_folder = f"{folder_id}/{'/'.join(path_parts[:-1])}"
            else:
                storage_folder = str(folder_id)
        else:
            storage_folder = str(folder_id)
        
        if settings.STORAGE_BACKEND == "s3":
            storage_key = await upload_file_to_s3(file, folder=storage_folder)
            storage_type = "s3"
        else:
            storage_key = save_file_locally(file, folder=storage_folder)
            storage_type = "local"

        db_file = create_file(db, FileCreate(filename=file.filename, folder_id=folder_id), current_user.id, storage_type, storage_key)
        db_file.storage_type = storage_type
        db_file.storage_key = storage_key
        db_file.file_size = len(file_content)
        db.commit()
        db.refresh(db_file)
        uploaded.append(db_file)
    
    return uploaded

@router.get("/{file_id}/download")
def download_file(
    file_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    folder = get_folder(db, file.folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check permissions for root folder
    if folder.parent_id is None:
        access_control = getattr(folder, 'access_control', None)
        if access_control:
            role = access_control.get(str(current_user.id)) or current_user.role
        else:
            role = current_user.role
        if role not in [RoleEnum.admin, RoleEnum.editor, RoleEnum.viewer]:
            raise HTTPException(status_code=403, detail="No download permission")
    
    if file.storage_type == "s3":
        url = get_s3_download_url(file.storage_key)
        return {"url": url}
    elif file.storage_type == "local":
        file_path = os.path.join(settings.LOCAL_UPLOADS_PATH, file.storage_key)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        mime_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'text/javascript',
            'json': 'application/json',
            'xml': 'text/xml',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        media_type = mime_types.get(file_ext, 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            filename=file.filename,
            media_type=media_type
        )
    else:
        raise HTTPException(status_code=500, detail="Unknown storage type")

@router.put("/{file_id}", response_model=FileOut)
def update_file_info(
    file_id: int, 
    file_update: FileUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id and current_user.role not in [RoleEnum.admin, RoleEnum.editor]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this file")
    
    return update_file(db, file_id, file_update)

@router.post("/{file_id}/move", response_model=FileOut)
def move_file_to_folder(
    file_id: int, 
    move_request: FileMove, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to move this file")
    
    return move_file(db, file_id, move_request.new_folder_id)

@router.delete("/{file_id}")
def delete_file_api(
    file_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.uploaded_by != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    if file.storage_type == "local":
        delete_local_file(file.storage_key)
    
    delete_file(db, file_id)
    
    return {"msg": "File deleted successfully"}