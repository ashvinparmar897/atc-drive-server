from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user import RoleEnum

class FolderPermission(Base):
    __tablename__ = "folder_permissions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(RoleEnum), nullable=False)  # e.g., 'editor' or 'viewer'

    folder = relationship("Folder", back_populates="permissions")
    user = relationship("User")