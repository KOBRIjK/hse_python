"""Проверка входных данных: имя владельца, суммы, время операции."""
import re
from datetime import datetime

# «Имя Фамилия»: два слова с заглавной буквы, оба на латинице
# или оба на кириллице
NAME_PATTERN = re.compile(
    r"^(?:[A-Z][a-z]+ [A-Z][a-z]+|[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+)$"
)


def validate_owner(value):
    """Возвращает имя владельца или бросает ValueError."""
    if not isinstance(value, str) or not NAME_PATTERN.match(value):
        raise ValueError(f"Некорректное имя владельца: {value!r}. "
                         f"Ожидается формат «Имя Фамилия»")
    return value


def to_number(value, what="Сумма"):
    """Проверяет, что value — число (bool не считается числом)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{what} должна быть числом, получено {value!r}")
    return float(value)


def validate_amount(amount):
    """Сумма операции должна быть положительным числом."""
    amount = to_number(amount)
    if not amount > 0:                  # заодно отсекает NaN
        raise ValueError(f"Сумма операции должна быть положительной, "
                         f"получено {amount}")
    return round(amount, 2)


def validate_timestamp(timestamp):
    """Возвращает время операции (по умолчанию — текущее)."""
    if timestamp is None:
        return datetime.now()
    if not isinstance(timestamp, datetime):
        raise TypeError("timestamp должен быть объектом datetime")
    return timestamp
