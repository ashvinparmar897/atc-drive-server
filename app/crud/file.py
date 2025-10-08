from sqlalchemy.orm import Session
from app.models.file import File
from app.schemas.file import FileCreate, FileUpdate, FileMove

def create_file(db: Session, file: FileCreate, uploaded_by: int, storage_type: str = "local", storage_key: str = None):
    db_file = File(
        filename=file.filename,
        folder_id=file.folder_id,
        uploaded_by=uploaded_by,
        storage_type=storage_type,
        storage_key=storage_key
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: int):
    return db.query(File).filter(File.id == file_id).first()

def update_file(db: Session, file_id: int, file_update: FileUpdate):
    db_file = get_file(db, file_id)
    if not db_file:
        return None
    
    update_data = file_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_file, field, value)
    
    db.commit()
    db.refresh(db_file)
    return db_file

def move_file(db: Session, file_id: int, new_folder_id: int):
    db_file = get_file(db, file_id)
    if not db_file:
        return None
    
    db_file.folder_id = new_folder_id
    db.commit()
    db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int):
    db_file = get_file(db, file_id)
    if not db_file:
        return False
    
    db.delete(db_file)
    db.commit()
    return True 