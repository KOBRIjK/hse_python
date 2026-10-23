"""Аналитика и визуализация по истории операций (DataFrame)."""
import matplotlib.pyplot as plt

from .constants import DEPOSIT, INTEREST, SUCCESS, WITHDRAW
from .validation import to_number


def large_operations(history, threshold, n):
    """Последние n успешных операций с суммой >= threshold."""
    threshold = to_number(threshold, "Порог")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("n должно быть положительным целым числом")
    mask = (history["status"] == SUCCESS) & (history["amount"] >= threshold)
    return history[mask].tail(n)


def plot_balance(history, title):
    """Линейный график баланса после операций во времени."""
    if history.empty:
        print("История пуста — строить нечего")
        return
    history = history.sort_values("timestamp", kind="stable")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(history["timestamp"], history["balance_after"], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Дата и время операции")
    ax.set_ylabel("Баланс после операции")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    plt.show()


def recalculate_balance(initial, history):
    """Пересчёт баланса по истории независимо от класса счёта.

    Начальный баланс плюс успешные пополнения и проценты минус
    успешные снятия.
    """
    ok = history[history["status"] == SUCCESS]
    sign = ok["operation"].map({DEPOSIT: 1, INTEREST: 1, WITHDRAW: -1})
    return round(initial + (ok["amount"] * sign).sum(), 2)
