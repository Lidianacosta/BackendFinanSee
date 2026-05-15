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
        """Cria um novo período (mês) para o usuário."""
        # Verifica se já existe esse mês para o usuário.
        statement = select(Period).where(
            col(Period.user_id) == user_id,
            col(Period.month) == period_create.month,
        )
        result = await self.session.exec(statement)
        if result.first():
            raise HTTPException(
                status_code=400, detail="Period already exists for this month"
            )

        # Busca a renda atual do usuário para inicializar o período se não for enviada
        user = await self.session.get(User, user_id)
        period_data = period_create.model_dump()

        # Se o total_income for 0 (default), usamos o do cadastro do usuário
        if period_data.get("total_income") == Decimal("0.0") and user:
            period_data["total_income"] = user.income

        period = Period(**period_data, user_id=user_id)
        self.session.add(period)
        await self.session.commit()
        await self.session.refresh(period)
        return period

    async def read_all(self, user_id: uuid.UUID) -> list[Period]:
        """Lista todos os períodos do usuário."""
        statement = (
            select(Period)
            .where(col(Period.user_id) == user_id)
            .order_by(col(Period.month).desc())
        )
        result = await self.session.exec(statement)
        return list(result.all())

    async def read(self, period_id: uuid.UUID, user_id: uuid.UUID) -> Period:
        """Busca um período específico."""
        period = await self.session.get(Period, period_id)
        if not period or period.user_id != user_id:
            raise HTTPException(status_code=404, detail="Period not found")
        return period

    async def get_or_create_by_date(
        self, user_id: uuid.UUID, date_val: date
    ) -> Period:
        """Busca um período pelo mês/ano ou cria um novo se não existir."""
        first_day = date_val.replace(day=1)
        statement = select(Period).where(
            col(Period.user_id) == user_id, col(Period.month) == first_day
        )
        result = await self.session.exec(statement)
        period = result.first()

        if not period:
            # Se não existir, cria usando a lógica de inicialização automática
            return await self.create(PeriodCreate(month=first_day), user_id)

        return period

    async def get_summary(
        self, period_id: uuid.UUID, user_id: uuid.UUID
    ) -> PeriodSummary:
        """Calcula o resumo financeiro do período."""
        period = await self.read(period_id, user_id)

        # Busca todas as despesas do período
        statement = select(Expense).where(col(Expense.period_id) == period_id)
        result = await self.session.exec(statement)
        expenses = result.all()

        total_paid = sum(
            (e.value for e in expenses if e.status == ExpenseEnum.PAGA),
            Decimal("0.0"),
        )
        total_pending = sum(
            (e.value for e in expenses if e.status == ExpenseEnum.A_PAGAR),
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
