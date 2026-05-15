"""Period service layer."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import col, select

from src.models.expenses import Expense, ExpenseEnum
from src.models.periods import Period
from src.models.users import User
from src.schemas.periods import PeriodCreate, PeriodSummary
from src.utils.database import AsyncSessionDep


class PeriodService:
    def __init__(self, session: AsyncSessionDep) -> None:
        self.session = session

    async def create(
        self, period_create: PeriodCreate, user_id: uuid.UUID
    ) -> Period:
        """Create a new financial period (month) for the user."""
        statement = select(Period).where(
            col(Period.user_id) == user_id,
            col(Period.month) == period_create.month,
        )
        result = await self.session.exec(statement)
        if result.first():
            raise HTTPException(
                status_code=400, detail="Já existe um período para este mês"
            )

        user = await self.session.get(User, user_id)
        period_data = period_create.model_dump()

        if period_data.get("total_income") == Decimal("0.0") and user:
            period_data["total_income"] = user.income

        period = Period(**period_data, user_id=user_id)
        self.session.add(period)
        await self.session.commit()
        await self.session.refresh(period)
        return period

    async def read_all(self, user_id: uuid.UUID) -> list[Period]:
        """List all financial periods for the user."""
        statement = (
            select(Period)
            .where(col(Period.user_id) == user_id)
            .order_by(col(Period.month).desc())
        )
        result = await self.session.exec(statement)
        return list(result.all())

    async def read(self, period_id: uuid.UUID, user_id: uuid.UUID) -> Period:
        """Retrieve a specific financial period."""
        period = await self.session.get(Period, period_id)
        if not period or period.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Período não encontrado",
            )
        return period

    async def get_or_create_by_date(
        self, user_id: uuid.UUID, date_val: date
    ) -> Period:
        """Retrieve a period by month/year or create a new one if it doesn't exist."""
        first_day = date_val.replace(day=1)
        statement = select(Period).where(
            col(Period.user_id) == user_id, col(Period.month) == first_day
        )
        result = await self.session.exec(statement)
        period = result.first()

        if not period:
            return await self.create(PeriodCreate(month=first_day), user_id)

        return period

    async def get_summary(
        self, period_id: uuid.UUID, user_id: uuid.UUID
    ) -> PeriodSummary:
        """Calculate the financial summary for the period."""
        period = await self.read(period_id, user_id)

        statement = select(Expense).where(col(Expense.period_id) == period_id)
        result = await self.session.exec(statement)
        expenses = result.all()

        total_paid = sum(
            (e.value or Decimal("0.0") for e in expenses if e.status == ExpenseEnum.PAID),
            Decimal("0.0"),
        )
        total_pending = sum(
            (e.value or Decimal("0.0") for e in expenses if e.status == ExpenseEnum.PENDING),
            Decimal("0.0"),
        )

        return PeriodSummary(
            month=period.month,
            total_income=period.total_income,
            total_expenses_paid=total_paid,
            total_expenses_pending=total_pending,
            remaining_balance=period.total_income - total_paid,
        )


PeriodServiceDep = Annotated[PeriodService, Depends(PeriodService)]
