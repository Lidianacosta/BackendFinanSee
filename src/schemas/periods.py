import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PeriodBase(BaseModel):
    month: date
    total_income: Decimal = Field(default=Decimal("0.0"), ge=0)


class PeriodCreate(PeriodBase):
    pass


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
