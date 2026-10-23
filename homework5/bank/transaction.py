"""Запись истории операций счёта."""
from dataclasses import dataclass
from datetime import datetime

from .constants import SOURCE_MANUAL


@dataclass(frozen=True)
class Transaction:
    """Одна запись истории операций счёта (неизменяемая)."""

    operation: str             # deposit / withdraw / interest
    amount: float              # сумма операции (всегда > 0)
    timestamp: datetime        # дата и время операции
    balance_after: float       # баланс после операции
    status: str                # success / fail
    reason: str = ""           # причина отказа для status == fail
    transfer_id: str = ""      # идентификатор перевода (если это перевод)
    counterparty: str = ""     # номер счёта второй стороны перевода
    source: str = SOURCE_MANUAL  # manual / transfer / import

    def __str__(self):
        line = (f"{self.timestamp:%Y-%m-%d %H:%M:%S} | "
                f"{self.operation:<8} | {self.amount:>10.2f} | "
                f"баланс {self.balance_after:>10.2f} | {self.status}")
        if self.transfer_id:
            line += f" | перевод {self.transfer_id} ({self.counterparty})"
        if self.reason:
            line += f" | {self.reason}"
        return line
