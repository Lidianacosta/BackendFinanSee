"""Unit tests for ReportService PDF generation."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.models.expenses import ExpenseEnum
from src.models.users import User
from src.schemas.expenses import ExpenseCreate
from src.schemas.periods import PeriodCreate
from src.services.expenses import ExpenseService
from src.services.periods import PeriodService
from src.services.reports import ReportService
from src.utils.password import get_password_hash


async def _make_user(db, email="rep@u.com", income=Decimal("2000")):
    user = User(
        name="Reporter",
        email=email,
        hashed_password=get_password_hash("password123"),
        income=income,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_generate_pdf_with_expenses(db):
    """Generating a PDF for a period with expenses should return bytes."""
    user = await _make_user(db)
    ps = PeriodService(db)
    es = ExpenseService(db)
    rs = ReportService(db, ps)

    p = await ps.create(
        PeriodCreate(month=date(2026, 2, 1), total_income=Decimal("1500")),
        user.id,
    )
    await es.create(
        ExpenseCreate(
            name="Conta de Luz",
            value=Decimal("200"),
            due_date=date(2026, 2, 10),
            status=ExpenseEnum.PENDING,
        ),
        user.id,
        ps,
    )

    pdf = await rs.generate_period_pdf(p.id, user)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_pdf_without_expenses(db):
    """Generating a PDF for an empty period should also succeed."""
    user = await _make_user(db, email="empty@u.com")
    ps = PeriodService(db)
    rs = ReportService(db, ps)

    p = await ps.create(
        PeriodCreate(month=date(2026, 5, 1), total_income=Decimal("1500")),
        user.id,
    )

    pdf = await rs.generate_period_pdf(p.id, user)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_pdf_period_not_found(db):
    """generate_period_pdf should 404 when the period does not exist."""
    user = await _make_user(db, email="nf@u.com")
    ps = PeriodService(db)
    rs = ReportService(db, ps)
    missing_period_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc:
        await rs.generate_period_pdf(missing_period_id, user)
    assert exc.value.status_code == 404


def test_get_month_name_for_all_months():
    """_get_month_name should return Portuguese names for every month."""
    from datetime import date

    rs = ReportService.__new__(ReportService)
    expected = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    for m, name in expected.items():
        assert rs._get_month_name(date(2026, m, 1)) == name
