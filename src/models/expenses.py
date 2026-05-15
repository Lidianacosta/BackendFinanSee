import uuid
from datetime import date as date_datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from src.models.base import BaseModel
from src.models.expense_category_link import ExpenseCategoryLink

if TYPE_CHECKING:
    from src.models.categories import Category
    from src.models.periods import Period
    from src.models.users import User


class ExpenseEnum(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"


class Expense(BaseModel, table=True):
    user_id: uuid.UUID | None = Field(
        foreign_key="user.id", ondelete="CASCADE"
    )
    user: "User" = Relationship(back_populates="expenses")

    categories: list["Category"] = Relationship(
        back_populates="expenses",
        link_model=ExpenseCategoryLink,
    )

    period_id: uuid.UUID | None = Field(
        foreign_key="period.id", ondelete="CASCADE"
    )
    period: "Period" = Relationship(back_populates="expenses")

    name: str | None = None

    value: Decimal | None = Field(default=Decimal("0.0"), decimal_places=2)

    due_date: date_datetime | None = Field(
        default_factory=date_datetime.today, nullable=True
    )
    payment_date: date_datetime | None = None
    description: str | None = None
    is_fixed: bool = False
    payment_method: str | None = None
    status: ExpenseEnum = Field(default=ExpenseEnum.PENDING)

    def __str__(self):
        return str(self.name)
