"""Data validation utilities.

Provides functions for validating CPF, phone numbers, names, descriptions,
and calculating age.
"""

import re
from datetime import date


def validate_cpf(cpf: str) -> bool:
    """Validate a Brazilian CPF."""
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        value = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True


def validate_phone(phone: str) -> bool:
    """Strictly validate Brazilian phone numbers (only 10 or 11 digits)."""
    numbers_only = re.sub(r"\D", "", phone)
    if len(numbers_only) != len(phone) or len(numbers_only) not in [10, 11]:
        return False
    return True


def calculate_age(birth_date: date) -> int:
    """Calculate the age based on the birth date."""
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def validate_name(name: str) -> bool:
    """Strict name validation: only letters and spaces."""
    return bool(re.fullmatch(r"[A-Za-zÀ-ÿ\s]+", name))


def validate_description(description: str) -> bool:
    """Strict description validation."""
    return bool(re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s.,!?-]+", description))
