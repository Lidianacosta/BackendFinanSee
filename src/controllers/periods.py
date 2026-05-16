import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.models.users import User
from src.schemas.periods import (
    ExpenseAnalysis,
    FinancialEvolution,
    PeriodCreate,
    PeriodRead,
    PeriodSummary,
)
from src.services.periods import PeriodServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/periods", tags=["Periods"])


@router.post(
    "/", response_model=PeriodRead, status_code=status.HTTP_201_CREATED
)
async def create_period(
    period_data: PeriodCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Create a new financial period (month) for the user."""
    return await service.create(period_data, current_user.id)


@router.get("/", response_model=list[PeriodRead])
async def read_periods(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """List all financial periods for the authenticated user."""
    return await service.read_all(current_user.id)


@router.get("/current/", response_model=PeriodRead)
async def read_current_period(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Retrieve the current financial period (auto-creates if missing)."""
    return await service.get_or_create_by_date(current_user.id, date.today())


@router.get("/{period_id}", response_model=PeriodRead)
async def read_period(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Retrieve details of a specific financial period."""
    return await service.read(period_id, current_user.id)


@router.get("/{period_id}/summary", response_model=PeriodSummary)
async def read_period_summary(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Return the financial summary (Balance, Paid/Pending Expenses) for the period."""
    return await service.get_summary(period_id, current_user.id)


@router.get("/{period_id}/evolution", response_model=FinancialEvolution)
async def read_period_evolution(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Return the financial evolution (7-month window) around the period."""
    return await service.get_financial_evolution(period_id, current_user.id)


@router.get("/{period_id}/analysis", response_model=ExpenseAnalysis)
async def read_period_analysis(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Return a detailed expense analysis (top category, daily average, 5-day intervals)."""
    return await service.get_expense_analysis(period_id, current_user.id)
