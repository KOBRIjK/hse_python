"""Базовый банковский счёт: общая логика учёта операций."""
import uuid
from dataclasses import asdict, fields

import pandas as pd

from .. import analytics
from ..constants import (DEPOSIT, FAIL, SOURCE_IMPORT, SOURCE_TRANSFER,
                         SUCCESS, WITHDRAW)
from ..data_import import ImportReport, clean_operations, read_file
from ..transaction import Transaction
from ..validation import (to_number, validate_amount, validate_owner,
                          validate_timestamp)


class BankAccount:
    """Базовый банковский счёт.

    Все изменения баланса проходят через _apply. Наследники меняют
    только «точки расширения»: allowed_operations и
    _withdraw_denial_reason.
    """

    account_type = "base"                   # переопределяется в наследниках
    type_title = "Базовый счёт"
    allowed_operations = (DEPOSIT, WITHDRAW)

    _next_number = 1000                     # общий счётчик номеров

    def __init__(self, owner, balance=0):
        self.owner = owner                  # валидация в сеттере
        balance = to_number(balance, "Начальный баланс")
        if balance < 0:
            raise ValueError("Начальный баланс не может быть отрицательным")
        self._balance = round(balance, 2)
        self._history = []
        self._number = self._generate_number()

    @staticmethod
    def _generate_number():
        """Возвращает следующий уникальный номер счёта ACC-XXXX."""
        # Счётчик хранится именно в BankAccount, чтобы номера
        # не повторялись у счетов разных типов
        number = f"ACC-{BankAccount._next_number}"
        BankAccount._next_number += 1
        return number

    # ----- свойства --------------------------------------------------

    @property
    def number(self):
        """Номер счёта (только чтение)."""
        return self._number

    @property
    def balance(self):
        """Текущий баланс (только чтение)."""
        return self._balance

    @property
    def owner(self):
        """Владелец счёта."""
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = validate_owner(value)

    @property
    def history(self):
        """Копия истории операций (список Transaction)."""
        return list(self._history)

    # ----- ядро учёта ------------------------------------------------

    def _withdraw_denial_reason(self, amount):
        """Причина отказа в снятии или пустая строка, если можно.

        Точка расширения: наследники добавляют свои ограничения.
        """
        if amount > self._balance:
            return "недостаточно средств"
        return ""

    def _record(self, operation, amount, timestamp, status, **extra):
        """Добавляет запись в историю и возвращает её."""
        transaction = Transaction(operation, amount, timestamp,
                                  self._balance, status, **extra)
        self._history.append(transaction)
        return transaction

    def _apply(self, operation, amount, timestamp=None, **extra):
        """Единая точка изменения баланса.

        Списание, которое запрещено правилами счёта, не меняет баланс,
        но фиксируется в истории со статусом fail.
        """
        if operation not in self.allowed_operations:
            raise ValueError(f"Операция {operation!r} недоступна для "
                             f"типа счёта {self.account_type!r}")
        amount = validate_amount(amount)
        timestamp = validate_timestamp(timestamp)

        if operation == WITHDRAW:
            reason = self._withdraw_denial_reason(amount)
            if reason:
                return self._record(operation, amount, timestamp, FAIL,
                                    reason=reason, **extra)
            self._balance = round(self._balance - amount, 2)
        else:                                   # deposit и interest
            self._balance = round(self._balance + amount, 2)
        return self._record(operation, amount, timestamp, SUCCESS, **extra)

    # ----- публичные операции ----------------------------------------

    def deposit(self, amount, timestamp=None):
        """Пополнение счёта. Возвращает запись истории."""
        return self._apply(DEPOSIT, amount, timestamp)

    def withdraw(self, amount, timestamp=None):
        """Снятие со счёта. Возвращает запись истории (success/fail)."""
        return self._apply(WITHDRAW, amount, timestamp)

    def transfer_to(self, other, amount, timestamp=None):
        """Перевод на другой счёт.

        Обе записи получают общий transfer_id и номер второй стороны.
        Если списание отклонено, получатель не затрагивается.
        Возвращает пару (запись отправителя, запись получателя или None).
        """
        if not isinstance(other, BankAccount):
            raise TypeError("Получатель должен быть банковским счётом")
        if other is self:
            raise ValueError("Нельзя перевести средства на тот же счёт")
        timestamp = validate_timestamp(timestamp)
        transfer_id = "TR-" + uuid.uuid4().hex[:8].upper()

        outgoing = self._apply(WITHDRAW, amount, timestamp,
                               transfer_id=transfer_id,
                               counterparty=other.number,
                               source=SOURCE_TRANSFER)
        if outgoing.status == FAIL:
            return outgoing, None
        incoming = other._apply(DEPOSIT, amount, timestamp,
                                transfer_id=transfer_id,
                                counterparty=self.number,
                                source=SOURCE_TRANSFER)
        return outgoing, incoming

    # ----- представление и аналитика ---------------------------------

    def history_df(self):
        """История операций в виде DataFrame."""
        columns = [f.name for f in fields(Transaction)]
        return pd.DataFrame([asdict(t) for t in self._history],
                            columns=columns)

    def print_history(self, last=None):
        """Печатает историю (все записи или последние last)."""
        records = self._history[-last:] if last else self._history
        print(f"История {self.number} ({self.owner}), "
              f"записей: {len(self._history)}")
        for transaction in records:
            print("  " + str(transaction))

    def large_operations(self, threshold, n):
        """Последние n успешных операций с суммой >= threshold."""
        return analytics.large_operations(self.history_df(), threshold, n)

    def plot_balance(self):
        """Линейный график баланса после операций во времени."""
        analytics.plot_balance(
            self.history_df(),
            f"Изменение баланса счёта {self.number} ({self.owner})")

    def __str__(self):
        return (f"{self.type_title} {self.number} | {self.owner} | "
                f"баланс {self._balance:.2f}")

    def __repr__(self):
        return (f"{type(self).__name__}(number={self.number!r}, "
                f"owner={self.owner!r}, balance={self._balance})")

    # ----- загрузка внешних данных -----------------------------------

    def load_history(self, path, source_account):
        """Загружает операции счёта source_account из CSV/JSON.

        Невалидные строки отбрасываются, валидные применяются в
        хронологическом порядке через _apply, поэтому баланс счёта
        соответствует последовательности принятых операций
        (balance_after из файла не используется). Строки со статусом
        fail попадают в историю как неуспешные и баланс не меняют.
        Возвращает ImportReport.
        """
        data = read_file(path)
        matched, accepted, rejected = clean_operations(
            data, source_account, self.account_type,
            self.allowed_operations)

        applied = []
        for row in accepted.itertuples(index=False):
            if row.status == SUCCESS:
                transaction = self._apply(row.operation, row.amount,
                                          row.date, source=SOURCE_IMPORT)
            else:
                # Неуспешная операция из файла: только запись в историю
                transaction = self._record(
                    row.operation, round(row.amount, 2), row.date, FAIL,
                    source=SOURCE_IMPORT)
            applied.append(transaction)

        return ImportReport(str(path), self.number, source_account,
                            len(data), len(matched), accepted, rejected,
                            applied)
