from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User")
    files = relationship("File", back_populates="folder")
    parent = relationship("Folder", remote_side=[id])
    permissions = relationship("FolderPermission", back_populates="folder", cascade="all, delete-orphan")