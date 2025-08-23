from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class Folder(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    access_control = Column(JSON, nullable=True)  # {user_id: role}
    owner = relationship("User")
    files = relationship("File", back_populates="folder")
    parent = relationship("Folder", remote_side=[id]) 