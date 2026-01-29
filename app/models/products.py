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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    product_name = Column(String(255), nullable=False)
    sku = Column(String(100))
    cost_price = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    description = Column(Text)
    attributes = Column(JSON, comment="Thuộc tính: size, color, weight, images...")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", backref="products")
    category = relationship("Category", backref="products")
    product_calculations = relationship(
        "ProductCalculation", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_category_id", "category_id"),
        Index("idx_sku", "sku"),
        Index("idx_product_name", "product_name"),
        Index("idx_is_active", "is_active"),
    )
