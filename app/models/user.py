from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String(255), nullable=False, unique=True)

    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=False)

    phone = Column(String(20), nullable=True, unique=True, index=True)

    preferences = Column(JSON)

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user_platforms = relationship("UserPlatform", back_populates="user")

    __table_args__ = (
        Index("idx_phone", "phone"),
        Index("idx_is_active", "is_active"),
    )
