"""Expense service layer."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.models.categories import Category
from src.models.expenses import Expense
from src.schemas.expenses import ExpenseCreate, ExpenseUpdate
from src.utils.database import AsyncSessionDep


from src.services.periods import PeriodService

class ExpenseService:
    def __init__(self, session: AsyncSessionDep) -> None:
        self.session = session

    async def create(
        self, 
        expense_create: ExpenseCreate, 
        user_id: uuid.UUID,
        period_service: PeriodService
    ) -> Expense:
        """Cria uma despesa e associa às categorias. Automaticamente resolve o período se necessário."""
        data = expense_create.model_dump(exclude={"category_ids", "period_id"})
        
        # Lógica de Automação do Período
        period_id = expense_create.period_id
        if not period_id:
            # Se não enviou o período, descobrimos pelo vencimento da despesa
            period = await period_service.get_or_create_by_date(user_id, expense_create.due_date)
            period_id = period.id

        expense = Expense(**data, user_id=user_id, period_id=period_id)

        # Associa categorias se fornecidas

        # Associa categorias se fornecidas
        if expense_create.category_ids:
            statement = select(Category).where(
                col(Category.id).in_(expense_create.category_ids),
                col(Category.user_id) == user_id,
            )
            result = await self.session.exec(statement)
            categories = result.all()
            expense.categories = list(categories)

        self.session.add(expense)
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    async def read_all(
        self, user_id: uuid.UUID, period_id: uuid.UUID | None = None
    ) -> list[Expense]:
        """Lista despesas, opcionalmente filtradas por período."""
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
        """Busca uma despesa específica."""
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
        """Atualiza uma despesa."""
        expense = await self.read(expense_id, user_id)
        data = expense_update.model_dump(
            exclude_unset=True, exclude={"category_ids"}
        )

        # Atualiza categorias se fornecidas
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
        return expense

    async def delete(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Deleta uma despesa."""
        expense = await self.read(expense_id, user_id)
        await self.session.delete(expense)
        await self.session.commit()


ExpenseServiceDep = Annotated[ExpenseService, Depends(ExpenseService)]
