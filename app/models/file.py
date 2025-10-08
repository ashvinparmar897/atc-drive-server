from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    folder_id = Column(Integer, ForeignKey('folders.id'))
    s3_key = Column(String, nullable=True)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    storage_type = Column(String, default="s3")  # 's3' or 'local'
    storage_key = Column(String, nullable=True)   # s3 key or local path
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    folder = relationship("Folder", back_populates="files")
    uploader = relationship("User", back_populates="files") 