"""User schema definitions.

Pydantic models for user data validation and API representation.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from src.utils.validators import calculate_age, validate_cpf, validate_phone


class UserBase(BaseModel):
    """Base schema for user profile data."""

    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    date_of_birth: date | None = None
    phone_number: str | None = Field(
        default=None, min_length=10, max_length=15
    )
    income: Decimal = Field(default=Decimal("0.0"), ge=0)

    @field_validator("cpf")
    @classmethod
    def check_cpf(cls, v: str | None) -> str | None:
        """Validate CPF format."""
        if v and not validate_cpf(v):
            raise ValueError("CPF inválido")
        return v

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        """Validate phone number format."""
        if v and not validate_phone(v):
            raise ValueError("Número de telefone inválido")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def check_age(cls, v: date | None) -> date | None:
        """Ensure the user is at least 18 years old."""
        if v and calculate_age(v) < 18:
            raise ValueError("O usuário deve ter pelo menos 18 anos")
        return v


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(min_length=8)
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        """Verify that password and confirmation password match."""
        if self.password != self.confirm_password:
            raise ValueError("As senhas não coincidem")
        return self


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""

    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    date_of_birth: date | None = None
    phone_number: str | None = Field(
        default=None, min_length=10, max_length=15
    )
    income: Decimal | None = Field(default=None, ge=0)
    password: str | None = Field(default=None, min_length=8)

    @field_validator("cpf")
    @classmethod
    def check_cpf(cls, v: str | None) -> str | None:
        """Validate CPF update."""
        if v and not validate_cpf(v):
            raise ValueError("CPF inválido")
        return v

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        """Validate phone update."""
        if v and not validate_phone(v):
            raise ValueError("Número de telefone inválido")
        return v


class UserRead(UserBase):
    """Schema for reading user data from the API."""

    id: uuid.UUID
    is_active: bool
    date_joined: datetime

    model_config = ConfigDict(from_attributes=True)
