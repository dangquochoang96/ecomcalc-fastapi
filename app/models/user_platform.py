from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    Index,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship


class UserPlatform(Base):
    __tablename__ = "user_platforms"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_id = Column(
        Integer,
        ForeignKey("platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shop_name = Column(String(255))
    shop_id = Column(String(100))
    is_default = Column(Boolean, default=False, index=True)

    # JSON metadata mapped to 'user_metadata' to avoid conflict with Base.metadata property
    user_metadata = Column("metadata", JSON)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tax_profile = Column(TINYINT, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    platform = relationship("Platform", back_populates="user_platforms")
    user = relationship("User", back_populates="user_platforms")
    category = relationship("Category", back_populates="user_platforms")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "platform_id", "shop_id", name="unique_user_platform_shop"
        ),
        Index("idx_shop_name", "shop_name"),
    )
