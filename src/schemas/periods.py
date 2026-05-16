import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from src.schemas.categories import CategoryRead


class PeriodBase(BaseModel):
    month: date
    total_income: Decimal = Field(default=Decimal("0.0"), ge=0)


class PeriodCreate(PeriodBase):
    @field_validator("month", mode="before")
    @classmethod
    def force_first_day_of_month(cls, v):
        if isinstance(v, date):
            return v.replace(day=1)
        if isinstance(v, str):
            d = date.fromisoformat(v)
            return d.replace(day=1)
        return v


class PeriodRead(PeriodBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PeriodSummary(BaseModel):
    month: date
    total_income: Decimal
    total_expenses_paid: Decimal
    total_expenses_pending: Decimal
    remaining_balance: Decimal


class PeriodMonthData(BaseModel):
    user_balance: Decimal
    monthly_expense: Decimal


class FinancialEvolutionEntry(BaseModel):
    month_abbreviation: str
    date: date
    data: PeriodMonthData


class FinancialEvolution(BaseModel):
    evolution: list[FinancialEvolutionEntry]


class DailyEvolutionEntry(BaseModel):
    start_date: date
    end_date: date
    total_expense: Decimal


class ExpenseAnalysis(BaseModel):
    id: uuid.UUID
    month: date
    monthly_expense: Decimal
    daily_average: Decimal
    category_that_appears_most: "CategoryRead | dict" = {}
    daily_evolution: list[DailyEvolutionEntry]

    model_config = ConfigDict(from_attributes=True)
