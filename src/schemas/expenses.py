from decimal import Decimal
from datetime import date
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.models.expenses import ExpenseEnum
from src.utils.validators import validate_name, validate_description
from src.schemas.categories import CategoryRead
from src.schemas.periods import PeriodRead

class ExpenseBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    value: Decimal = Field(ge=0, decimal_places=2)
    due_date: date
    description: str | None = Field(default=None, max_length=500)
    is_fixed: bool = False
    payment_method: str | None = Field(default=None, max_length=100)
    status: ExpenseEnum = ExpenseEnum.A_PAGAR

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        if not validate_name(v):
            raise ValueError("Name contains invalid characters")
        return v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        if v and not validate_description(v):
            raise ValueError("Description contains invalid characters")
        return v

class ExpenseCreate(ExpenseBase):
    period_id: uuid.UUID | None = None
    category_ids: list[uuid.UUID] = []

class ExpenseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    value: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    due_date: date | None = None
    payment_date: date | None = None
    description: str | None = Field(default=None, max_length=500)
    is_fixed: bool | None = None
    payment_method: str | None = Field(default=None, max_length=100)
    status: ExpenseEnum | None = None
    category_ids: list[uuid.UUID] | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v and not validate_name(v):
            raise ValueError("Name contains invalid characters")
        return v

class ExpenseRead(ExpenseBase):
    id: uuid.UUID
    user_id: uuid.UUID
    period_id: uuid.UUID
    period: PeriodRead | None = None
    categories: list[CategoryRead] = []
    payment_date: date | None = None

    model_config = ConfigDict(from_attributes=True)
