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
    period_id: Annotated[uuid.UUID | None, Query()] = None,
    search: Annotated[
        str | None, Query(description="Search by name")
    ] = None,
    category_ids: Annotated[
        list[uuid.UUID] | None,
        Query(description="Filter by category IDs"),
    ] = None,
    expense_status: Annotated[
        ExpenseEnum | None,
        Query(alias="status", description="Filter by status"),
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """List expenses with advanced filtering and pagination."""
    return await service.read_all(
        user_id=current_user.id,
        period_id=period_id,
        search=search,
        category_ids=category_ids,
        status=expense_status,
        offset=offset,
        limit=limit,
    )


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
