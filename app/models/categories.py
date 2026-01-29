from sqlalchemy import (
    Column,
    Integer,
    String,
    SmallInteger,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    platform_id = Column(
        Integer,
        ForeignKey("platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_name = Column(String(255), nullable=False)

    category_code = Column(String(100), nullable=True)

    level = Column(Integer, nullable=True)

    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    description = Column(Text)

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Quan hệ self-referential
    parent = relationship("Category", remote_side=[id], back_populates="children")

    children = relationship("Category", back_populates="parent")

    # Quan hệ với category fees
    category_fees = relationship(
        "CategoryFee",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    user_platforms = relationship("UserPlatform", back_populates="category")

    __table_args__ = (
        UniqueConstraint("platform_id", "category_code", name="unique_category"),
        Index("idx_platform_id", "platform_id"),
        Index("idx_parent_id", "parent_id"),
        Index("idx_level", "level"),
        Index("idx_is_active", "is_active"),
        Index("idx_level_parent", "level", "parent_id"),
    )


class CategoryFee(Base):
    __tablename__ = "category_fees"

    id = Column(Integer, primary_key=True)

    platform_fee_id = Column(
        Integer, ForeignKey("platform_fees.id", ondelete="CASCADE"), nullable=False
    )

    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    shop_type = Column(SmallInteger, nullable=False)

    fee_value = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Quan hệ với category
    category = relationship("Category", back_populates="category_fees", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "platform_fee_id", "category_id", "shop_type", name="unique_fee_category"
        ),
        Index("idx_platform_fee_id", "platform_fee_id"),
        Index("idx_category_id", "category_id"),
        Index("idx_category_fee", "category_id", "platform_fee_id"),
    )
