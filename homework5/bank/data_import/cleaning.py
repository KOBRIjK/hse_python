"""Очистка «грязных» строк перед загрузкой в историю счёта."""
import pandas as pd

from ..constants import KNOWN_OPERATIONS, KNOWN_STATUSES
from .readers import parse_date


def row_problems(row, account_type, allowed_operations):
    """Список причин, по которым строка файла невалидна для счёта."""
    problems = []

    if str(row["account_type"]).strip() != account_type:
        problems.append("тип счёта в файле не совпадает")

    operation = str(row["operation"] or "").strip()
    if not operation:
        problems.append("пустой тип операции")
    elif operation not in KNOWN_OPERATIONS:
        problems.append(f"опечатка в типе операции ({operation})")
    elif operation not in allowed_operations:
        problems.append(f"{operation} недопустим для счёта "
                        f"типа {account_type}")

    amount = pd.to_numeric(row["amount"], errors="coerce")
    if pd.isna(amount):
        raw = row["amount"]
        empty = raw is None or str(raw).strip() in ("", "nan")
        problems.append("пустая сумма" if empty else "сумма не число")
    elif amount <= 0:
        problems.append("неположительная сумма")

    if parse_date(row["date"]) is None:
        problems.append("некорректная дата")

    if str(row["status"]).strip() not in KNOWN_STATUSES:
        problems.append(f"некорректный статус ({row['status']})")
    return problems


def clean_operations(data, source_account, account_type,
                     allowed_operations):
    """Отбирает строки счёта и делит их на принятые и отклонённые.

    Возвращает (matched, accepted, rejected):
    matched  — все строки счёта source_account;
    accepted — валидные строки с приведёнными типами, по дате;
    rejected — невалидные строки с колонкой reason.
    """
    matched = data[data["account_number"].astype(str).str.strip()
                   == source_account].copy()

    reasons = matched.apply(row_problems, axis=1,
                            args=(account_type, allowed_operations))
    reasons = reasons.map("; ".join)
    # Полные дубликаты строк считаем ошибкой выгрузки
    duplicated = matched.duplicated(keep="first")
    reasons[duplicated] = reasons[duplicated].map(
        lambda text: "; ".join(filter(None, ["дубликат строки", text]))
    )
    matched["reason"] = reasons

    rejected = matched[matched["reason"] != ""]
    accepted = matched[matched["reason"] == ""].drop(columns="reason")
    accepted = accepted.assign(
        date=accepted["date"].map(parse_date),
        amount=pd.to_numeric(accepted["amount"]),
        operation=accepted["operation"].str.strip(),
        status=accepted["status"].str.strip(),
    ).sort_values("date", kind="stable")
    return matched.drop(columns="reason"), accepted, rejected
