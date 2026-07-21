"""Unit tests for models.

Tests model methods and field integrity.
"""

from datetime import date

from src.models.categories import Category
from src.models.expenses import Expense
from src.models.periods import Period
from src.models.users import User


def test_models_str_methods():
    """Test __str__ methods of models."""
    assert str(User(email="test@test.com")) == "test@test.com"
    assert str(Category(name="Food")) == "Food"
    assert str(Expense(name="Lunch")) == "Lunch"


def test_period_model_logic():
    """Test Period model validation logic."""
    assert Period.force_first_day_of_month(date(2023, 5, 15)) == date(
        2023, 5, 1
    )
    assert Period.force_first_day_of_month("2023-05-15") == date(2023, 5, 1)
    assert Period.force_first_day_of_month(123) == 123
