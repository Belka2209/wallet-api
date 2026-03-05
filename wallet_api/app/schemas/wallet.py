from decimal import Decimal
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class OperationType(str, Enum):
    "Type of wallet operation"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletBase(BaseModel):
    "Base schema for wallet responses"
    uuid: UUID


class WalletResponse(WalletBase):
    "Schema for wallet responses"
    balance: Decimal = Field(..., ge=0, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OperationRequest(BaseModel):
    "Schema for wallet operation requests"
    operation_type: OperationType
    amount: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("amount")
    def validate_amount(cls, v):
        "Validate that amount is greater than 0 and has at most 2 decimal places"
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount must have at most 2 decimal places")
        return v


class OperationResponse(BaseModel):
    "Schema for wallet operation responses"
    uuid: UUID
    balance: Decimal
    operation_type: OperationType
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    "Schema for error responses"
    detail: str
