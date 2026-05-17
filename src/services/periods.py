"""Period service layer."""

import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select

from src.models.categories import Category
from src.models.expenses import Expense, ExpenseEnum
from src.models.periods import Period
from src.models.users import User
from src.schemas.periods import (
    DailyEvolutionEntry,
    ExpenseAnalysis,
    FinancialEvolution,
    FinancialEvolutionEntry,
    PeriodCreate,
    PeriodMonthData,
    PeriodSummary,
)
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
            (
                e.value or Decimal("0.0")
                for e in expenses
                if e.status == ExpenseEnum.PAID
            ),
            Decimal("0.0"),
        )
        total_pending = sum(
            (
                e.value or Decimal("0.0")
                for e in expenses
                if e.status == ExpenseEnum.PENDING
            ),
            Decimal("0.0"),
        )

        return PeriodSummary(
            month=period.month,
            total_income=period.total_income,
            total_expenses_paid=total_paid,
            total_expenses_pending=total_pending,
            remaining_balance=period.total_income - total_paid,
        )

    async def get_financial_evolution(
        self, period_id: uuid.UUID, user_id: uuid.UUID
    ) -> FinancialEvolution:
        """Get financial data for 3 months back and 3 months forward."""
        current_period = await self.read(period_id, user_id)
        evolution = []

        for i in range(-3, 4):
            target_month = current_period.month.month + i
            target_year = current_period.month.year

            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1

            target_date = date(target_year, target_month, 1)

            statement = select(Period).where(
                col(Period.user_id) == user_id,
                col(Period.month) == target_date,
            )
            result = await self.session.exec(statement)
            period = result.first()

            if period:
                exp_statement = select(func.sum(Expense.value)).where(
                    col(Expense.period_id) == period.id
                )
                exp_result = await self.session.exec(exp_statement)
                total_exp = exp_result.one() or Decimal("0.0")

                data = PeriodMonthData(
                    user_balance=period.total_income, monthly_expense=total_exp
                )
            else:
                data = PeriodMonthData(
                    user_balance=Decimal("0.0"), monthly_expense=Decimal("0.0")
                )

            evolution.append(
                FinancialEvolutionEntry(
                    month_abbreviation=target_date.strftime("%b"),
                    date=target_date,
                    data=data,
                )
            )

        return FinancialEvolution(evolution=evolution)

    async def get_expense_analysis(
        self, period_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExpenseAnalysis:
        """Get detailed expense analysis for the period."""
        period = await self.read(period_id, user_id)

        statement = (
            select(Expense)
            .where(col(Expense.period_id) == period_id)
            .options(selectinload(Expense.categories))
        )
        result = await self.session.exec(statement)
        expenses = list(result.all())

        total_expense = sum(
            (e.value or Decimal("0.0") for e in expenses), Decimal("0.0")
        )

        category_counts = {}
        for exp in expenses:
            for cat in exp.categories:
                category_counts[cat.id] = category_counts.get(cat.id, 0) + 1

        top_category = {}
        if category_counts:
            top_cat_id = max(category_counts, key=category_counts.get)
            top_cat_obj = await self.session.get(Category, top_cat_id)
            if top_cat_obj:
                from src.schemas.categories import CategoryRead

                top_category = CategoryRead.model_validate(top_cat_obj)

        _, last_day = monthrange(period.month.year, period.month.month)
        daily_average = (
            total_expense / last_day if last_day > 0 else Decimal("0.0")
        )

        daily_evolution = []
        for start_day in range(1, last_day + 1, 5):
            end_day = min(start_day + 4, last_day)
            start_dt = period.month.replace(day=start_day)
            end_dt = period.month.replace(day=end_day)

            interval_total = sum(
                (
                    e.value or Decimal("0.0")
                    for e in expenses
                    if e.due_date and start_dt <= e.due_date <= end_dt
                ),
                Decimal("0.0"),
            )
            daily_evolution.append(
                DailyEvolutionEntry(
                    start_date=start_dt,
                    end_date=end_dt,
                    total_expense=interval_total,
                )
            )

        return ExpenseAnalysis(
            id=period.id,
            month=period.month,
            monthly_expense=total_expense,
            daily_average=daily_average,
            category_that_appears_most=top_category,
            daily_evolution=daily_evolution,
        )


PeriodServiceDep = Annotated[PeriodService, Depends(PeriodService)]
