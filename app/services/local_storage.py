import os
from fastapi import UploadFile
from uuid import uuid4
from app.core.config import settings

def save_file_locally(file: UploadFile, folder: str = "") -> str:
    # Create uploads directory if it doesn't exist
    uploads_dir = settings.LOCAL_UPLOADS_PATH
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Create folder directory if specified
    if folder:
        dir_path = os.path.join(uploads_dir, folder)
        os.makedirs(dir_path, exist_ok=True)
    else:
        dir_path = uploads_dir
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"{uuid4()}.{ext}" if ext else str(uuid4())
    
    # Save file
    file_path = os.path.join(dir_path, filename)
    
    # Read file content and write to disk
    file_content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Return relative path from uploads directory
    return os.path.relpath(file_path, uploads_dir)

def get_local_file_url(key: str) -> str:
    return f"/files/local/{key}"

def delete_local_file(key: str) -> bool:
    try:
        file_path = os.path.join(settings.LOCAL_UPLOADS_PATH, key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False