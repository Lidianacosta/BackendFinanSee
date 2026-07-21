"""Category database model for FinanSee.

Categories help users organize their expenses.
"""

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from src.models.base import BaseModel
from src.models.expense_category_link import ExpenseCategoryLink

if TYPE_CHECKING:
    from src.models.expenses import Expense
    from src.models.users import User


class Category(BaseModel, table=True):
    """Represents a category for expenses."""

    name: str | None = Field(default=None, unique=True)
    description: str | None = None
    user_id: uuid.UUID | None = Field(
        foreign_key="user.id", ondelete="CASCADE"
    )
    user: "User" = Relationship(back_populates="categories")

    expenses: list["Expense"] = Relationship(
        back_populates="categories",
        link_model=ExpenseCategoryLink,
    )

    def __str__(self):
        """Returns the string representation of the category."""
        return str(self.name)
