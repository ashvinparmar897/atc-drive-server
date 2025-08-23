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

# Allow all file types like Google Drive
ALLOWED_EXTENSIONS = {
    # Images
    "png", "jpg", "jpeg", "gif", "bmp", "svg", "webp", "ico", "tiff", "tif",
    # Documents
    "pdf", "doc", "docx", "txt", "rtf", "odt", "pages",
    # Spreadsheets
    "xls", "xlsx", "csv", "ods", "numbers",
    # Presentations
    "ppt", "pptx", "odp", "key",
    # Archives
    "zip", "rar", "7z", "tar", "gz", "bz2",
    # Code files
    "py", "js", "html", "css", "php", "java", "cpp", "c", "cs", "ts", "jsx", "tsx",
    "json", "xml", "yaml", "yml", "md", "sql", "sh", "bat", "ps1",
    # Design files
    "ai", "psd", "cdr", "eps", "indd", "sketch", "fig",
    # CAD files
    "dwg", "dxf", "stp", "step", "iges", "x_t", "x_b",
    # Video files
    "mp4", "avi", "mov", "wmv", "flv", "webm", "mkv", "m4v",
    # Audio files
    "mp3", "wav", "flac", "aac", "ogg", "wma", "m4a",
    # Other common files
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
        # Get files in root (folder_id is None)
        files = db.query(FileModel).filter(FileModel.folder_id == None).all()
    else:
        # Get files with specific folder_id
        files = db.query(FileModel).filter(FileModel.folder_id == int(folder_id)).all()
    return files

@router.post("/upload", response_model=List[FileOut])
async def upload_files(folder_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail="Too many files (max 100)")
    
    folder = get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if folder.parent_id is None and folder.access_control:
        role = folder.access_control.get(str(current_user.id)) or current_user.role
        if role not in [RoleEnum.admin, RoleEnum.editor]:
            raise HTTPException(status_code=403, detail="No upload permission")
    
    uploaded = []
    for file in files:
        # Check file extension (case insensitive)
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        # Allow all file types (like Google Drive)
        # if ext not in ALLOWED_EXTENSIONS:
        #     raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Reset file position for storage
        await file.seek(0)
        
        # Handle folder uploads - check if file has a path structure
        file_path = getattr(file, 'path', '') or file.filename
        if '/' in file_path:
            # This is a folder upload, create subfolder structure
            path_parts = file_path.split('/')
            if len(path_parts) > 1:
                # Create subfolder path
                subfolder_path = '/'.join(path_parts[:-1])
                storage_folder = f"{folder_id}/{subfolder_path}"
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

        db_file = create_file(db, FileCreate(filename=file.filename, folder_id=folder_id), None, current_user.id)
        db_file.storage_type = storage_type
        db_file.storage_key = storage_key
        db.commit()
        db.refresh(db_file)
        uploaded.append(db_file)
    
    return uploaded

@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    folder = get_folder(db, file.folder_id)
    if folder.parent_id is None and folder.access_control:
        role = folder.access_control.get(str(current_user.id)) or current_user.role
        if role not in [RoleEnum.admin, RoleEnum.editor, RoleEnum.viewer]:
            raise HTTPException(status_code=403, detail="No download permission")
    
    if file.storage_type == "s3":
        url = get_s3_download_url(file.storage_key)
        return {"url": url}
    elif file.storage_type == "local":
        # Return file directly for local storage
        file_path = os.path.join(settings.LOCAL_UPLOADS_PATH, file.storage_key)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Get file extension for proper MIME type
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
    
    # Check if user owns the file or has admin rights
    if file.uploaded_by != current_user.id and current_user.role != RoleEnum.admin:
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
    
    # Check if user owns the file or has admin rights
    if file.uploaded_by != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to move this file")
    
    return move_file(db, file_id, move_request.new_folder_id)

@router.delete("/{file_id}")
def delete_file_api(file_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if user owns the file or has admin rights
    if file.uploaded_by != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    # Delete from storage
    if file.storage_type == "local":
        delete_local_file(file.storage_key)
    
    # Delete from database
    delete_file(db, file_id)
    
    return {"msg": "File deleted successfully"} 