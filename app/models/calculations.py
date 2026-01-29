from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    DECIMAL,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FeeCalculation(Base):
    __tablename__ = "fee_calculations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    platform_id = Column(
        Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False
    )
    calculation_name = Column(String(255))
    calculation_date = Column(DateTime, server_default=func.now())
    notes = Column(Text)
    fee_config = Column(JSON, comment="Cấu hình phí đã áp dụng trong phiên này")

    # Statistics
    total_products = Column(Integer, default=0)
    total_revenue = Column(DECIMAL(15, 2), default=0)
    total_fees = Column(DECIMAL(15, 2), default=0)
    total_profit = Column(DECIMAL(15, 2), default=0)
    avg_profit_margin = Column(DECIMAL(10, 2), default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", backref="fee_calculations")
    platform = relationship("Platform", backref="fee_calculations")
    product_calculations = relationship(
        "ProductCalculation",
        back_populates="fee_calculation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_platform_id", "platform_id"),
        Index("idx_calculation_date", "calculation_date"),
        Index("idx_total_profit", "total_profit"),
    )


class ProductCalculation(Base):
    __tablename__ = "product_calculations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fee_calculation_id = Column(
        Integer, ForeignKey("fee_calculations.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )

    cost_price = Column(DECIMAL(15, 2), nullable=False)
    selling_price = Column(DECIMAL(15, 2), nullable=False)
    total_fees = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    net_profit = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    profit_margin = Column(DECIMAL(10, 2))
    revenue = Column(DECIMAL(15, 2))

    fee_breakdown = Column(JSON, comment="Chi tiết từng loại phí đã tính")

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    fee_calculation = relationship(
        "FeeCalculation", back_populates="product_calculations"
    )
    product = relationship("Product", back_populates="product_calculations")

    __table_args__ = (
        Index("idx_fee_calculation_id", "fee_calculation_id"),
        Index("idx_product_id", "product_id"),
        Index("idx_net_profit", "net_profit"),
        Index("idx_profit_margin", "profit_margin"),
    )
