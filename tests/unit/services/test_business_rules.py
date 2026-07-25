"""Unit tests for business rules and edge cases."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.models.expenses import ExpenseEnum
from src.schemas.categories import CategoryCreate
from src.schemas.expenses import ExpenseCreate, ExpenseUpdate
from src.schemas.periods import PeriodCreate
from src.services.categories import CategoryService
from src.services.expenses import ExpenseService
from src.services.periods import PeriodService


@pytest.mark.asyncio
async def test_cannot_delete_category_with_expenses(db):
    """Test deleting a category that has expenses associated."""
    uid = uuid.uuid4()
    cs = CategoryService(db)
    es = ExpenseService(db)
    ps = PeriodService(db)

    # Create category and period
    cat = await cs.create(CategoryCreate(name="Alimentação"), uid)

    # Add an expense to this category
    await es.create(
        ExpenseCreate(
            name="Almoço",
            value=Decimal("50.0"),
            due_date=date(2023, 1, 15),
            category_ids=[cat.id],
            status=ExpenseEnum.PAID,
        ),
        uid,
        ps,
    )

    # Attempt to delete should raise HTTPException 400
    with pytest.raises(HTTPException) as exc:
        await cs.delete(cat.id, uid)

    assert exc.value.status_code == 400
    assert (
        "Não é possível deletar uma categoria que possui despesas"
        in exc.value.detail
    )


@pytest.mark.asyncio
async def test_cannot_pay_already_paid_expense(db):
    """Test paying an expense that is already paid."""
    uid = uuid.uuid4()
    es = ExpenseService(db)
    ps = PeriodService(db)

    exp = await es.create(
        ExpenseCreate(
            name="Conta de Luz",
            value=Decimal("150.0"),
            due_date=date(2023, 1, 15),
            status=ExpenseEnum.PAID,
        ),
        uid,
        ps,
    )

    update_data = ExpenseUpdate(status=ExpenseEnum.PAID)

    with pytest.raises(HTTPException) as exc:
        await es.update(exp.id, update_data, uid)

    assert exc.value.status_code == 400
    assert "A despesa já está paga" in exc.value.detail


@pytest.mark.asyncio
async def test_cannot_create_duplicate_period(db):
    """Test creating a period for a month that already has one."""
    uid = uuid.uuid4()
    ps = PeriodService(db)

    await ps.create(
        PeriodCreate(month=date(2023, 1, 1), total_income=Decimal("1000")), uid
    )

    duplicate_period = PeriodCreate(
        month=date(2023, 1, 15), total_income=Decimal("2000")
    )

    with pytest.raises(HTTPException) as exc:
        await ps.create(duplicate_period, uid)

    assert exc.value.status_code == 400
    assert "Já existe um período para este mês" in exc.value.detail


@pytest.mark.asyncio
async def test_financial_evolution_without_expenses(db):
    """Test financial evolution report when a period has no expenses."""
    uid = uuid.uuid4()
    ps = PeriodService(db)

    p = await ps.create(
        PeriodCreate(month=date(2023, 1, 1), total_income=Decimal("1000")), uid
    )

    evo = await ps.get_financial_evolution(p.id, uid)

    # Should not break, should return 0 balances or just the income
    assert evo is not None
    # Just verifying it executes without ZeroDivisionError or IndexError
