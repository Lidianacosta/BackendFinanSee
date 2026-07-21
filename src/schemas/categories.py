"""Category schema definitions.

Pydantic models for category data validation and API representation.
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.utils.validators import validate_description, validate_name


class CategoryBase(BaseModel):
    """Base schema for category data."""

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        """Validate that the category name contains only allowed characters."""
        if not validate_name(v):
            raise ValueError("Nome contém caracteres inválidos")
        return v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        """Validate that the category description contains only allowed characters."""
        if v and not validate_description(v):
            raise ValueError("Descrição contém caracteres inválidos")
        return v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        """Validate name update."""
        if v and not validate_name(v):
            raise ValueError("Nome contém caracteres inválidos")
        return v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        """Validate description update."""
        if v and not validate_description(v):
            raise ValueError("Descrição contém caracteres inválidos")
        return v


class CategoryRead(CategoryBase):
    """Schema for reading category data from the API."""

    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
