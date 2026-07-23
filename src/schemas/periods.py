"""Financial period schema definitions.

Pydantic models for period data validation, API representation, and analytics.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from src.schemas.categories import CategoryRead


class PeriodBase(BaseModel):
    """Base schema for period data."""

    month: date
    total_income: Decimal = Field(default=Decimal("0.0"), ge=0)


class PeriodCreate(PeriodBase):
    """Schema for creating a new financial period."""

    @field_validator("month", mode="before")
    @classmethod
    def force_first_day_of_month(cls, v):
        """Normalize the input date to the first day of its month."""
        if isinstance(v, date):
            return v.replace(day=1)
        if isinstance(v, str):
            d = date.fromisoformat(v)
            return d.replace(day=1)
        return v


class PeriodRead(PeriodBase):
    """Schema for reading period data from the API."""

    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PeriodSummary(BaseModel):
    """Financial summary for a specific period."""

    month: date
    total_income: Decimal
    total_expenses_paid: Decimal
    total_expenses_pending: Decimal
    remaining_balance: Decimal


class PeriodMonthData(BaseModel):
    """Data for a single month in a financial series."""

    user_balance: Decimal
    monthly_expense: Decimal


class FinancialEvolutionEntry(BaseModel):
    """A single entry in a financial evolution series."""

    month_abbreviation: str
    date: date
    data: PeriodMonthData


class FinancialEvolution(BaseModel):
    """A collection of evolution entries representing a timeframe."""

    evolution: list[FinancialEvolutionEntry]


class DailyEvolutionEntry(BaseModel):
    """Expense aggregation for a specific interval within a month."""

    start_date: date
    end_date: date
    total_expense: Decimal


class ExpenseAnalysis(BaseModel):
    """Comprehensive analysis of expenses for a specific period."""

    id: uuid.UUID
    month: date
    monthly_expense: Decimal
    daily_average: Decimal
    category_that_appears_most: "CategoryRead | dict" = {}
    daily_evolution: list[DailyEvolutionEntry]

    model_config = ConfigDict(from_attributes=True)


# Resolve forward reference to CategoryRead without an end-of-file
# import (would trigger ruff E402). Pydantic rebuild uses the imported
# symbol available at runtime via src.schemas.categories below.
from src.schemas.categories import CategoryRead  # noqa: E402 F811

ExpenseAnalysis.model_rebuild()
