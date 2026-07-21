"""Financial period endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.models.users import User
from src.schemas.periods import (
    ExpenseAnalysis,
    FinancialEvolution,
    PeriodCreate,
    PeriodRead,
    PeriodSummary,
)
from src.services.periods import PeriodServiceDep
from src.services.reports import ReportServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/periods", tags=["Periods"])


@router.post(
    "/", response_model=PeriodRead, status_code=status.HTTP_201_CREATED
)
async def create_period(
    period_data: PeriodCreate,
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a new financial period."""
    return await service.create(period_data, current_user.id)


@router.get("/", response_model=list[PeriodRead])
async def read_periods(
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """List all financial periods for the current user."""
    return await service.read_all(current_user.id)


@router.get("/current/", response_model=PeriodRead)
async def read_current_period(
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Retrieve or create the financial period for the current month."""
    from datetime import date

    return await service.get_or_create_by_date(current_user.id, date.today())


@router.get("/{period_id}", response_model=PeriodRead)
async def read_period(
    period_id: uuid.UUID,
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Retrieve a specific financial period."""
    return await service.read(period_id, current_user.id)


@router.get("/{period_id}/summary", response_model=PeriodSummary)
async def read_period_summary(
    period_id: uuid.UUID,
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get financial summary for a period."""
    return await service.get_summary(period_id, current_user.id)


@router.get("/{period_id}/evolution", response_model=FinancialEvolution)
async def read_financial_evolution(
    period_id: uuid.UUID,
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get financial evolution analytics."""
    return await service.get_financial_evolution(period_id, current_user.id)


@router.get("/{period_id}/analysis", response_model=ExpenseAnalysis)
async def read_expense_analysis(
    period_id: uuid.UUID,
    service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get detailed expense analysis."""
    return await service.get_expense_analysis(period_id, current_user.id)


@router.get("/{period_id}/export")
async def export_period_pdf(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    report_service: ReportServiceDep,
):
    """Export period data as a PDF report."""
    pdf_content = await report_service.generate_period_pdf(
        period_id, current_user
    )
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{period_id}.pdf"
        },
    )
