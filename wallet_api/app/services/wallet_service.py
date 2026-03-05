from decimal import Decimal
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.wallet import Wallet
from app.schemas.wallet import OperationType


class WalletService:
    "Service class for wallet operations"
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wallet(self, wallet_uuid: UUID) -> Optional[Wallet]:
        """Get wallet by UUID"""
        query = select(Wallet).where(Wallet.uuid == str(wallet_uuid))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_wallet_balance(self, wallet_uuid: UUID) -> Optional[Decimal]:
        """Get wallet balance by UUID"""
        wallet = await self.get_wallet(wallet_uuid)
        return wallet.balance if wallet else None

    async def create_wallet(self) -> Wallet:
        """Create a new wallet"""
        wallet = Wallet()
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def update_balance(
        self, wallet_uuid: UUID, operation_type: OperationType, amount: Decimal
    ) -> Optional[Wallet]:
        """
        Update wallet balance with proper locking to handle concurrency
        """
        # Начинаем транзакцию
        async with self.db.begin():
            # Получаем кошелек с блокировкой FOR UPDATE
            query = (
                select(Wallet).where(Wallet.uuid == str(wallet_uuid)).with_for_update()
            )

            result = await self.db.execute(query)
            wallet = result.scalar_one_or_none()

            if not wallet:
                return None

            # Проверяем достаточно ли средств для снятия
            current_balance = Decimal(str(wallet.balance))

            if operation_type == OperationType.WITHDRAW:
                if current_balance < amount:
                    raise ValueError("Insufficient funds")
                new_balance = current_balance - amount
            else:  # DEPOSIT
                new_balance = current_balance + amount

            # Обновляем баланс
            wallet.balance = new_balance

            # Сохраняем изменения
            self.db.add(wallet)

            # Коммит произойдет при выходе из контекстного менеджера

        # Обновляем объект из БД
        await self.db.refresh(wallet)
        return wallet
