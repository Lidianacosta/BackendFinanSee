"""Unit tests for validators and schemas.

Tests utility validation functions and Pydantic schema constraints.
"""

from datetime import date

import pytest

from src.schemas.categories import CategoryBase, CategoryUpdate
from src.schemas.expenses import ExpenseBase, ExpenseUpdate
from src.schemas.periods import PeriodCreate
from src.schemas.users import UserBase, UserCreate, UserUpdate
from src.utils.validators import (
    validate_cpf,
    validate_description,
    validate_name,
    validate_phone,
)


def test_utils_validators():
    """Test individual utility validator functions."""
    assert validate_cpf("11111111111") is False
    assert validate_cpf("12345678908") is False
    assert validate_phone("123456789;") is False
    assert validate_phone("123") is False
    assert validate_phone("11999999999") is True
    assert validate_name("!") is False
    assert validate_description("🚀") is False


def test_schemas_validators():
    """Test Pydantic schema validation logic."""
    with pytest.raises(ValueError):
        CategoryBase(name="!")
    with pytest.raises(ValueError):
        CategoryBase(name="Valid", description="🚀")
    with pytest.raises(ValueError):
        CategoryUpdate(name="!")
    with pytest.raises(ValueError):
        CategoryUpdate(description="🚀")

    with pytest.raises(ValueError):
        ExpenseBase(name="!", value=10, due_date=date.today())
    with pytest.raises(ValueError):
        ExpenseBase(
            name="Valid", value=10, due_date=date.today(), description="🚀"
        )
    with pytest.raises(ValueError):
        ExpenseUpdate(name="!")

    with pytest.raises(ValueError):
        UserBase(name="Test", email="t@t.com", date_of_birth=date.today())
    with pytest.raises(ValueError):
        UserBase(name="Test", email="t@t.com", phone_number="!")
    with pytest.raises(ValueError):
        UserBase(name="Test", email="t@t.com", cpf="123")

    with pytest.raises(ValueError):
        UserCreate(
            name="Test",
            email="t@t.com",
            password="password123",
            confirm_password="diff",
            income=100,
        )

    with pytest.raises(ValueError):
        UserUpdate(cpf="123")
    with pytest.raises(ValueError):
        UserUpdate(phone_number="!")

    assert PeriodCreate.force_first_day_of_month(123) == 123
