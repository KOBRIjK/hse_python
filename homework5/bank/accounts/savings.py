"""Сберегательный счёт."""
from ..constants import DEPOSIT, INTEREST, WITHDRAW
from ..validation import to_number
from .base import BankAccount


class SavingsAccount(BankAccount):
    """Сберегательный счёт: проценты и лимит снятия 50 % баланса."""

    account_type = "savings"
    type_title = "Сберегательный счёт"
    allowed_operations = (DEPOSIT, WITHDRAW, INTEREST)
    WITHDRAW_LIMIT = 0.5          # доля баланса, которую можно снять

    def _withdraw_denial_reason(self, amount):
        """Добавляет к базовым правилам лимит снятия 50 %."""
        reason = super()._withdraw_denial_reason(amount)
        if not reason and amount > self._balance * self.WITHDRAW_LIMIT:
            reason = (f"превышен лимит снятия "
                      f"{self.WITHDRAW_LIMIT:.0%} баланса")
        return reason

    def add_interest(self, rate_percent, timestamp=None):
        """Начисляет проценты на текущий остаток (ставка в %, напр. 7)."""
        rate = to_number(rate_percent, "Ставка")
        if rate <= 0:
            raise ValueError("Ставка должна быть положительной")
        interest = round(self._balance * rate / 100, 2)
        if interest <= 0:
            raise ValueError("Нечего начислять: баланс равен нулю")
        return self._apply(INTEREST, interest, timestamp)
