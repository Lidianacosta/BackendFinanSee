from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.categories import Category
    from src.models.expenses import Expense
    from src.models.periods import Period


class User(BaseModel, table=True):
    name: str | None = None
    email: str | None = Field(default=None, unique=True, nullable=True)
    hashed_password: str = Field()
    cpf: str | None = Field(default=None, unique=True, nullable=True)
    date_of_birth: date | None = Field(default=None, nullable=True)
    phone_number: str | None = Field(default=None, unique=True, nullable=True)
    income: Decimal | None = Field(default=Decimal("0.0"), decimal_places=2)
    is_staff: bool = False
    is_active: bool = True
    date_joined: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    categories: list["Category"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    expenses: list["Expense"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    periods: list["Period"] = Relationship(
        back_populates="user", cascade_delete=True
    )

    def __str__(self):
        return str(self.email)
