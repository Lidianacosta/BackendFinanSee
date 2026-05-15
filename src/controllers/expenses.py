import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

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
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: ExpenseServiceDep,
    period_service: PeriodServiceDep,
):
    """Create a new expense for the authenticated user."""
    return await service.create(expense_data, current_user.id, period_service)


@router.get("/", response_model=list[ExpenseRead])
async def read_expenses(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: ExpenseServiceDep,
    period_id: uuid.UUID | None = None,
):
    """List expenses for the authenticated user, with optional period filtering."""
    return await service.read_all(current_user.id, period_id)


@router.get("/{expense_id}", response_model=ExpenseRead)
async def read_expense(
    expense_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: ExpenseServiceDep,
):
    """Retrieve details of a specific expense."""
    return await service.read(expense_id, current_user.id)


@router.patch("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: uuid.UUID,
    expense_data: ExpenseUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: ExpenseServiceDep,
):
    """Update an existing expense."""
    return await service.update(expense_id, expense_data, current_user.id)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: ExpenseServiceDep,
):
    """Remove an expense from the system."""
    await service.delete(expense_id, current_user.id)
