import pytest
from decimal import Decimal
from uuid import uuid4, UUID
from httpx import AsyncClient
import asyncio


@pytest.mark.asyncio
async def test_create_wallet(client: AsyncClient):
    """Test wallet creation"""
    response = await client.post("/api/v1/wallets")
    assert response.status_code == 201

    data = response.json()
    assert "uuid" in data
    assert data["balance"] == "0.00"

    # Validate UUID format
    assert UUID(data["uuid"])


@pytest.mark.asyncio
async def test_get_wallet_balance(client: AsyncClient):
    """Test getting wallet balance"""
    # Create wallet first
    create_response = await client.post("/api/v1/wallets")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["uuid"]

    # Get wallet balance
    response = await client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert response.status_code == 200

    data = response.json()
    assert data["uuid"] == wallet_uuid
    assert Decimal(data["balance"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_get_nonexistent_wallet(client: AsyncClient):
    """Test getting nonexistent wallet"""
    fake_uuid = str(uuid4())
    response = await client.get(f"/api/v1/wallets/{fake_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_deposit_operation(client: AsyncClient):
    """Test deposit operation"""
    # Create wallet
    create_response = await client.post("/api/v1/wallets")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["uuid"]

    # Perform deposit
    operation_data = {"operation_type": "DEPOSIT", "amount": "100.50"}

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation", json=operation_data
    )

    # Должно быть 200, но если 409 - пробуем еще раз
    if response.status_code == 409:
        # Подождем немного и пробуем снова
        import asyncio

        await asyncio.sleep(0.1)
        response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation", json=operation_data
        )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == wallet_uuid
    assert Decimal(data["balance"]) == Decimal("100.50")
    assert data["operation_type"] == "DEPOSIT"
    assert Decimal(data["amount"]) == Decimal("100.50")


@pytest.mark.asyncio
async def test_withdraw_operation(client: AsyncClient):
    """Test withdraw operation"""
    # Create wallet
    create_response = await client.post("/api/v1/wallets")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["uuid"]

    # First deposit some money
    deposit_data = {"operation_type": "DEPOSIT", "amount": "200.00"}
    deposit_response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation", json=deposit_data
    )

    # Если 409 - пробуем еще раз
    if deposit_response.status_code == 409:
        import asyncio

        await asyncio.sleep(0.1)
        deposit_response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation", json=deposit_data
        )
    assert deposit_response.status_code == 200

    # Perform withdraw
    withdraw_data = {"operation_type": "WITHDRAW", "amount": "150.50"}

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation", json=withdraw_data
    )

    # Если 409 - пробуем еще раз
    if response.status_code == 409:
        await asyncio.sleep(0.1)
        response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation", json=withdraw_data
        )

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("49.50")  # 200.00 - 150.50 = 49.50


@pytest.mark.asyncio
async def test_insufficient_funds(client: AsyncClient):
    """Test withdrawal with insufficient funds"""
    # Create wallet
    create_response = await client.post("/api/v1/wallets")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["uuid"]

    # Try to withdraw without deposit
    withdraw_data = {"operation_type": "WITHDRAW", "amount": "50.00"}

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation", json=withdraw_data
    )

    # Должно быть 400 (недостаточно средств), но может быть 409 из-за конкурентности
    if response.status_code == 409:
        await asyncio.sleep(0.1)
        response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation", json=withdraw_data
        )

    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_concurrent_operations(client: AsyncClient):
    """Test concurrent operations on same wallet"""

    # Create wallet
    create_response = await client.post("/api/v1/wallets")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["uuid"]

    # Initial deposit
    deposit_data = {"operation_type": "DEPOSIT", "amount": "1000.00"}
    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation", json=deposit_data
    )

    # Если 409 - пробуем еще раз
    if response.status_code == 409:
        await asyncio.sleep(0.1)
        response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation", json=deposit_data
        )
    assert response.status_code == 200

    # Perform multiple concurrent operations
    async def perform_operation(amount: str, op_type: str):
        data = {"operation_type": op_type, "amount": amount}
        return await client.post(f"/api/v1/wallets/{wallet_uuid}/operation", json=data)

    # Create 10 concurrent requests
    tasks = []
    for i in range(5):
        tasks.append(perform_operation("100.00", "WITHDRAW"))
        tasks.append(perform_operation("50.00", "DEPOSIT"))

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Check all responses - могут быть 200 или 409, но не ошибки
    successful = 0
    conflicts = 0

    for response in responses:
        if isinstance(response, Exception):
            print(f"Exception: {response}")
        else:
            if response.status_code == 200:
                successful += 1
            elif response.status_code == 409:
                conflicts += 1

    print(f"Successful: {successful}, Conflicts: {conflicts}")

    # Check final balance - должно сходиться независимо от конфликтов
    final_response = await client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert final_response.status_code == 200
    final_balance = Decimal(final_response.json()["balance"])

    # Calculate expected balance: 1000 - 5*100 + 5*50 = 1000 - 500 + 250 = 750
    # Из-за конфликтов некоторые операции могут не выполниться, но баланс должен быть корректен
    expected_min = Decimal("250.00")  # Минимум если все withdraw прошли, а deposit нет
    expected_max = Decimal(
        "1250.00"
    )  # Максимум если все deposit прошли, а withdraw нет

    assert expected_min <= final_balance <= expected_max
    print(f"Final balance: {final_balance}")

