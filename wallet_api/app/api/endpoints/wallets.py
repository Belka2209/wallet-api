from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.schemas.wallet import (
    WalletResponse,
    OperationRequest,
    OperationResponse,
    ErrorResponse,
)
from app.services.wallet_service import WalletService
from sqlalchemy import create_engine

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])
# Можно настроить размер кэша
engine = create_engine(
    "postgresql+asyncpg://...",
    query_cache_size=0,  # Отключить кэширование запросов
)


@router.get(
    "/{wallet_uuid}",
    response_model=WalletResponse,
    responses={404: {"model": ErrorResponse, "description": "Wallet not found"}},
)
async def get_wallet_balance(wallet_uuid: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get wallet balance by UUID
    """
    service = WalletService(db)
    wallet = await service.get_wallet(wallet_uuid)

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
        )

    return wallet


@router.post(
    "/{wallet_uuid}/operation",
    response_model=OperationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Wallet not found"},
        409: {"model": ErrorResponse, "description": "Concurrent modification"},
    },
)
async def perform_operation(
    wallet_uuid: UUID, operation: OperationRequest, db: AsyncSession = Depends(get_db)
):
    """
    Perform deposit or withdraw operation on wallet
    """
    service = WalletService(db)

    try:
        updated_wallet = await service.update_balance(
            wallet_uuid, operation.operation_type, operation.amount
        )

        if not updated_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
            )

        return OperationResponse(
            uuid=wallet_uuid,
            balance=updated_wallet.balance,
            operation_type=operation.operation_type,
            amount=operation.amount,
        )

    except ValueError as e:
        # Ошибка недостаточности средств
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        # Ошибка базы данных (включая deadlock)
        print(f"SQLAlchemyError: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Operation failed due to database error",
        )
    except Exception as e:
        # Другие неожиданные ошибки
        print(f"Unexpected error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(db: AsyncSession = Depends(get_db)):
    """
    Create a new wallet (utility endpoint)
    """
    service = WalletService(db)
    wallet = await service.create_wallet()
    return wallet
