"""Expense service layer."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.models.categories import Category
from src.models.expenses import Expense
from src.schemas.expenses import ExpenseCreate, ExpenseUpdate
from src.services.periods import PeriodService
from src.utils.database import AsyncSessionDep


class ExpenseService:
    def __init__(self, session: AsyncSessionDep) -> None:
        self.session = session

    async def create(
        self,
        expense_create: ExpenseCreate,
        user_id: uuid.UUID,
        period_service: PeriodService,
    ) -> Expense:
        """Create an expense and associate it with categories. Automatically resolves the period if necessary."""
        data = expense_create.model_dump(exclude={"category_ids", "period_id"})

        period_id = expense_create.period_id
        if not period_id:
            period = await period_service.get_or_create_by_date(
                user_id, expense_create.due_date
            )
            period_id = period.id

        expense = Expense(**data, user_id=user_id, period_id=period_id)

        if expense_create.category_ids:
            statement = select(Category).where(
                col(Category.id).in_(expense_create.category_ids),
                col(Category.user_id) == user_id,
            )
            result = await self.session.exec(statement)
            expense.categories = list(result.all())

        self.session.add(expense)
        await self.session.commit()
        await self.session.refresh(expense)

        # Eager load relationships after creation to avoid lazy load errors in response
        return await self.read(expense.id, user_id)

    async def read_all(
        self, user_id: uuid.UUID, period_id: uuid.UUID | None = None
    ) -> list[Expense]:
        """List expenses, optionally filtered by period."""
        statement = (
            select(Expense)
            .where(col(Expense.user_id) == user_id)
            .options(
                selectinload(Expense.categories), selectinload(Expense.period)
            )
        )
        if period_id:
            statement = statement.where(col(Expense.period_id) == period_id)

        statement = statement.order_by(col(Expense.due_date).desc())
        result = await self.session.exec(statement)
        return list(result.all())

    async def read(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> Expense:
        """Retrieve a specific expense."""
        statement = (
            select(Expense)
            .where(
                col(Expense.id) == expense_id, col(Expense.user_id) == user_id
            )
            .options(
                selectinload(Expense.categories), selectinload(Expense.period)
            )
        )
        result = await self.session.exec(statement)
        expense = result.first()
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense

    async def update(
        self,
        expense_id: uuid.UUID,
        expense_update: ExpenseUpdate,
        user_id: uuid.UUID,
    ) -> Expense:
        """Update an expense."""
        expense = await self.read(expense_id, user_id)
        data = expense_update.model_dump(
            exclude_unset=True, exclude={"category_ids"}
        )

        if expense_update.category_ids is not None:
            statement = select(Category).where(
                col(Category.id).in_(expense_update.category_ids),
                col(Category.user_id) == user_id,
            )
            result = await self.session.exec(statement)
            expense.categories = list(result.all())

        for attr, value in data.items():
            setattr(expense, attr, value)

        self.session.add(expense)
        await self.session.commit()
        await self.session.refresh(expense)
        return await self.read(expense.id, user_id)

    async def delete(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete an expense."""
        expense = await self.read(expense_id, user_id)
        await self.session.delete(expense)
        await self.session.commit()


ExpenseServiceDep = Annotated[ExpenseService, Depends(ExpenseService)]
