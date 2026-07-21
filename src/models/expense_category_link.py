"""Link model for the many-to-many relationship between Expenses and Categories."""

import uuid

from sqlmodel import Field, SQLModel


class ExpenseCategoryLink(SQLModel, table=True):
    """Many-to-many relationship link between Expense and Category."""

    category_id: uuid.UUID | None = Field(
        default=None, foreign_key="category.id", primary_key=True
    )
    expense_id: uuid.UUID | None = Field(
        default=None, foreign_key="expense.id", primary_key=True
    )
