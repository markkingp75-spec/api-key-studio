import secrets
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class StudioUser(Base):
    __tablename__ = "studio_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    tier = Column(String, default="free")
    api_key = Column(String, unique=True, index=True, default=lambda: f"sk_live_{secrets.token_urlsafe(32)}")
    is_admin = Column(Boolean, default=False)
    status = Column(String, default="active")
    
    posts = relationship("Post", back_populates="owner")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("studio_users.id"))
    platform = Column(String)
    content = Column(String)
    media_url = Column(String, nullable=True)
    status = Column(String, default="pending")
    
    owner = relationship("StudioUser", back_populates="posts")