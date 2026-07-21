"""Expense endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.models.expenses import ExpenseEnum
from src.models.users import User
from src.schemas.expenses import ExpenseCreate, ExpenseRead, ExpenseUpdate
from src.services.expenses import ExpenseServiceDep
from src.services.periods import PeriodServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED
)
async def create_expense(
    expense_data: ExpenseCreate,
    service: ExpenseServiceDep,
    period_service: PeriodServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a new expense."""
    return await service.create(expense_data, current_user.id, period_service)


@router.get("/", response_model=list[ExpenseRead])
async def read_expenses(
    service: ExpenseServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
    period_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    category_ids: list[uuid.UUID] | None = Query(None),
    expense_status: ExpenseEnum | None = Query(None, alias="status"),
    offset: int = 0,
    limit: int = 100,
):
    """List expenses with filtering."""
    return await service.read_all(
        current_user.id,
        period_id,
        search,
        category_ids,
        expense_status,
        offset,
        limit,
    )


@router.get("/{expense_id}", response_model=ExpenseRead)
async def read_expense(
    expense_id: uuid.UUID,
    service: ExpenseServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Retrieve a specific expense."""
    return await service.read(expense_id, current_user.id)


@router.patch("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: uuid.UUID,
    expense_data: ExpenseUpdate,
    service: ExpenseServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update an expense."""
    return await service.update(expense_id, expense_data, current_user.id)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    service: ExpenseServiceDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete an expense."""
    await service.delete(expense_id, current_user.id)
