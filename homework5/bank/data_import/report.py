"""Отчёт об отбраковке строк при загрузке истории."""
from dataclasses import dataclass, field

import pandas as pd

from ..constants import FAIL


@dataclass
class ImportReport:
    """Результат загрузки истории из внешнего файла."""

    source: str                   # путь к файлу
    account_number: str           # номер счёта, в который грузили
    source_account: str           # номер счёта в файле
    rows_total: int               # всего строк в файле
    rows_matched: int             # строк, относящихся к счёту
    accepted: pd.DataFrame        # принятые строки
    rejected: pd.DataFrame        # отклонённые строки с колонкой reason
    applied: list = field(default_factory=list)  # созданные записи

    @property
    def denied_by_rules(self):
        """Принятые строки, которые счёт отклонил по своим правилам."""
        return [t for t in self.applied if t.status == FAIL and t.reason]

    def reasons_summary(self):
        """Количество отклонённых строк по каждой причине."""
        if self.rejected.empty:
            return pd.Series(dtype=int, name="rows")
        reasons = self.rejected["reason"].str.split("; ").explode()
        return reasons.value_counts().rename("rows")

    def print_summary(self):
        """Печатает краткую сводку загрузки."""
        print(f"Файл: {self.source}")
        print(f"Счёт {self.account_number} <- записи {self.source_account}")
        print(f"Строк в файле: {self.rows_total}, "
              f"относятся к счёту: {self.rows_matched}")
        print(f"Принято: {len(self.accepted)}, "
              f"отклонено: {len(self.rejected)}")
        if self.denied_by_rules:
            print(f"Из принятых отклонено правилами счёта: "
                  f"{len(self.denied_by_rules)}")
        if not self.rejected.empty:
            print("\nПричины отклонения:")
            for reason, count in self.reasons_summary().items():
                print(f"  - {reason}: {count}")
