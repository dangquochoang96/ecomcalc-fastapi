from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    DECIMAL,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    config = Column(
        JSON, comment="Cấu hình: logo_url, api_endpoint, default_currency..."
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    fees = relationship(
        "PlatformFee", back_populates="platform", cascade="all, delete-orphan"
    )
    user_platforms = relationship("UserPlatform", back_populates="platform")

    __table_args__ = (
        Index("idx_code", "code"),
        Index("idx_is_active", "is_active"),
    )


class PlatformFee(Base):
    __tablename__ = "platform_fees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(
        Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False
    )
    fee_name = Column(String(255), nullable=False)
    fee_code = Column(String(50), nullable=False)
    fee_type = Column(Integer, nullable=False)
    default_value = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    min_value = Column(DECIMAL(10, 2), default=0.00)
    max_value = Column(DECIMAL(10, 2), default=None)
    is_mandatory = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    platform = relationship("Platform", back_populates="fees")

    __table_args__ = (
        Index("idx_platform_id", "platform_id"),
        Index("idx_fee_type", "fee_type"),
        Index("idx_is_active", "is_active"),
        Index("idx_sort_order", "sort_order"),
    )
