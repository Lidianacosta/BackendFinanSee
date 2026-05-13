import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.expenses import Expense
    from src.models.users import User


class Period(BaseModel, table=True):
    user_id: uuid.UUID | None = Field(
        foreign_key="user.id", ondelete="CASCADE"
    )
    user: "User" = Relationship(back_populates="periods")

    month: date = Field(default_factory=date.today, index=True)
    total_income: Decimal = Field(
        default=Decimal("0.0"), decimal_places=2, ge=0
    )

    expenses: list["Expense"] = Relationship(back_populates="period")

    __table_args__ = (
        UniqueConstraint("user_id", "month", name="unique_user_period"),
    )

    @field_validator("month", mode="before")
    @classmethod
    def force_first_day_of_month(cls, v):
        if isinstance(v, date):
            return v.replace(day=1)
        if isinstance(v, str):
            d = date.fromisoformat(v)
            return d.replace(day=1)
        return v
