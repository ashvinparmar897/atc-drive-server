from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    folders = relationship("Folder", back_populates="owner")
    files = relationship("File", back_populates="uploader")

class Folder(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    access_control = Column(JSON, nullable=True)  # {user_id: role}
    owner = relationship("User", back_populates="folders")
    files = relationship("File", back_populates="folder")
    parent = relationship("Folder", remote_side=[id])

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    folder_id = Column(Integer, ForeignKey('folders.id'))
    s3_key = Column(String)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    folder = relationship("Folder", back_populates="files")
    uploader = relationship("User", back_populates="files") 