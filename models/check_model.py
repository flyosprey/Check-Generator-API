from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(
        Integer, ForeignKey("checks.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    checks = relationship("Checks", back_populates="products")


class Checks(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    payment_type = Column(String, nullable=False)
    buyer_name = Column(String, nullable=False)
    payment_amount = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    rest = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)

    owner = relationship("Users", back_populates="checks")
    products = relationship(
        "Products", back_populates="checks", cascade="all, delete-orphan"
    )
