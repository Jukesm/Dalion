from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    mp_user_id = Column(String, nullable=True)
    mp_access_token = Column(String, nullable=True)
    mp_refresh_token = Column(String, nullable=True)
    
    is_admin = Column(Boolean, default=False)
    
    # Scheduling & Persistence
    is_active = Column(Boolean, default=True)
    last_run_at = Column(Text, nullable=True) # ISO string
    created_at = Column(Float, default=lambda: datetime.utcnow().timestamp()) # Epoch for easier calc

    ideas = relationship("Idea", back_populates="owner")

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    target_audience = Column(String)
    description = Column(Text)
    price = Column(Float)
    status = Column(String, default="pending")  # pending, approved, rejected
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="ideas")

    # Analytics
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(Float, default=lambda: datetime.utcnow().timestamp())

    @property
    def conversion_rate(self) -> float:
        if self.views == 0:
            return 0.0
        return round((self.conversions / self.views) * 100, 2)
