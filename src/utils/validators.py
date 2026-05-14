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
    """Simple regex for Brazilian phone numbers: (XX) 9XXXX-XXXX or XXXXXXXXXXX."""
    phone = re.sub(r"\D", "", phone)
    return len(phone) in [10, 11]


def calculate_age(birth_date: date) -> int:
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def validate_name(name: str) -> bool:
    """Original name_regex_validator logic: only letters and spaces."""
    return bool(re.match(r"^[A-Za-zÀ-ÿ\s]+$", name))


def validate_description(description: str) -> bool:
    """Original description regex: letters, numbers, spaces, and common punctuation."""
    return bool(re.match(r"^[A-Za-zÀ-ÿ0-9\s.,!?-]+$", description))
