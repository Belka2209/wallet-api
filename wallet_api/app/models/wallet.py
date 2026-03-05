from uuid import uuid4
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Wallet(Base):
    """SQLAlchemy model for wallet"""
    __tablename__ = "wallets"

    uuid = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid4())
    )
    balance = Column(
        Numeric(10, 2), nullable=False, default=0.00, server_default="0.00"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        "Return string representation of wallet"
        return f"<Wallet(uuid={self.uuid}, balance={self.balance})>"

    @property
    def balance_decimal(self) -> Decimal:
        "Return balance as Decimal with 2 decimal places"
        return Decimal(str(self.balance))
