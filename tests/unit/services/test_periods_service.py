"""Unit tests for PeriodService business rules."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.models.expenses import ExpenseEnum
from src.schemas.expenses import ExpenseCreate
from src.schemas.periods import PeriodCreate
from src.services.expenses import ExpenseService
from src.services.periods import PeriodService


@pytest.mark.asyncio
async def test_read_period_not_found(db):
    """read() raises 404 for unknown period_id."""
    ps = PeriodService(db)
    period_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await ps.read(period_id, user_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_read_period_belongs_to_other_user_fails(db):
    """read() should 404 when the period belongs to another user."""
    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()
    ps = PeriodService(db)
    period = await ps.create(
        PeriodCreate(month=date(2026, 1, 1), total_income=Decimal("100")),
        uid_a,
    )
    with pytest.raises(HTTPException) as exc:
        await ps.read(period.id, uid_b)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_or_create_creates_when_missing(db):
    """get_or_create_by_date should create a period when none exists."""
    uid = uuid.uuid4()
    ps = PeriodService(db)
    p = await ps.get_or_create_by_date(uid, date(2026, 3, 15))
    assert p.month == date(2026, 3, 1)
    assert p.total_income == Decimal("0.0")


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(db):
    """get_or_create_by_date should return the existing period if present."""
    uid = uuid.uuid4()
    ps = PeriodService(db)
    p1 = await ps.create(
        PeriodCreate(month=date(2026, 5, 1), total_income=Decimal("500")), uid
    )
    p2 = await ps.get_or_create_by_date(uid, date(2026, 5, 20))
    assert p2.id == p1.id


@pytest.mark.asyncio
async def test_create_period_with_zero_income_inherits_user_income(db):
    """Period with total_income=0 should inherit income from the user."""
    from src.models.users import User
    from src.utils.password import get_password_hash

    user = User(
        name="X",
        email="x@test.com",
        hashed_password=get_password_hash("password123"),
        income=Decimal("3000"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    ps = PeriodService(db)
    p = await ps.create(PeriodCreate(month=date(2026, 1, 1)), user.id)
    assert p.total_income == Decimal("3000")


@pytest.mark.asyncio
async def test_get_summary_mixed_paid_pending_expenses(db):
    """get_summary should correctly aggregate paid and pending expenses."""
    uid = uuid.uuid4()
    ps = PeriodService(db)
    es = ExpenseService(db)

    p = await ps.create(
        PeriodCreate(month=date(2026, 1, 1), total_income=Decimal("1000")),
        uid,
    )
    await es.create(
        ExpenseCreate(
            name="Pago",
            value=Decimal("200"),
            due_date=date(2026, 1, 10),
            status=ExpenseEnum.PAID,
        ),
        uid,
        ps,
    )
    await es.create(
        ExpenseCreate(
            name="Pendente",
            value=Decimal("150"),
            due_date=date(2026, 1, 20),
            status=ExpenseEnum.PENDING,
        ),
        uid,
        ps,
    )

    summary = await ps.get_summary(p.id, uid)
    assert summary.total_expenses_paid == Decimal("200")
    assert summary.total_expenses_pending == Decimal("150")
    assert summary.remaining_balance == Decimal("800")  # 1000 - 200


@pytest.mark.asyncio
async def test_get_summary_period_not_found(db):
    """get_summary should propagate the 404 from read()."""
    ps = PeriodService(db)
    period_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await ps.get_summary(period_id, user_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_financial_evolution_with_periods_in_adjacent_months(db):
    """Evolution should pick up periods in adjacent months when present."""
    uid = uuid.uuid4()
    ps = PeriodService(db)
    await ps.create(
        PeriodCreate(month=date(2026, 1, 1), total_income=Decimal("1000")),
        uid,
    )
    await ps.create(
        PeriodCreate(month=date(2026, 2, 1), total_income=Decimal("1200")),
        uid,
    )

    p_jan = await ps.get_or_create_by_date(uid, date(2026, 1, 10))
    evo = await ps.get_financial_evolution(p_jan.id, uid)

    assert len(evo.evolution) == 7
    balances = [e.data.user_balance for e in evo.evolution]
    assert Decimal("1000") in balances
    assert Decimal("1200") in balances


@pytest.mark.asyncio
async def test_financial_evolution_period_not_found(db):
    """Evolution should 404 when the period does not exist."""
    ps = PeriodService(db)
    period_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await ps.get_financial_evolution(period_id, user_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_expense_analysis_with_top_category_tie(db):
    """When two categories tie, analysis should still return a valid one."""
    from src.schemas.categories import CategoryCreate
    from src.services.categories import CategoryService

    uid = uuid.uuid4()
    ps = PeriodService(db)
    es = ExpenseService(db)
    cs = CategoryService(db)

    p = await ps.create(
        PeriodCreate(month=date(2026, 1, 1), total_income=Decimal("1000")),
        uid,
    )
    cat_a = await cs.create(CategoryCreate(name="Alpha"), uid)
    cat_b = await cs.create(CategoryCreate(name="Beta"), uid)

    await es.create(
        ExpenseCreate(
            name="Compra Teste",
            value=Decimal("50"),
            due_date=date(2026, 1, 5),
            status=ExpenseEnum.PENDING,
            category_ids=[cat_a.id, cat_b.id],
        ),
        uid,
        ps,
    )

    analysis = await ps.get_expense_analysis(p.id, uid)
    assert analysis.monthly_expense == Decimal("50")
    # last_day=31, daily_average = 50/31
    assert analysis.daily_average > Decimal("0")
    assert len(analysis.daily_evolution) > 0


@pytest.mark.asyncio
async def test_expense_analysis_period_not_found(db):
    """analysis should 404 when the period does not exist."""
    ps = PeriodService(db)
    period_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await ps.get_expense_analysis(period_id, user_id)
    assert exc.value.status_code == 404
