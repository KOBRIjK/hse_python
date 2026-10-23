"""Расчётный счёт."""
from .base import BankAccount


class CheckingAccount(BankAccount):
    """Расчётный счёт: пополнение и снятие без доп. ограничений."""

    account_type = "checking"
    type_title = "Расчётный счёт"
