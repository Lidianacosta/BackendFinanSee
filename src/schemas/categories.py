import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.utils.validators import validate_name


class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        if not validate_name(v):
            raise ValueError("Name contains invalid characters")
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v and not validate_name(v):
            raise ValueError("Name contains invalid characters")
        return v


class CategoryRead(CategoryBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
