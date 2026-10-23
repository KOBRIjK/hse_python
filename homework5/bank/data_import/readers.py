"""Чтение внешних файлов с операциями и разбор дат."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

# Форматы дат, которые встречаются во внешних файлах
DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M")


def read_file(path):
    """Читает CSV или JSON в DataFrame без преобразования типов."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        # dtype=str: сохраняем «сырые» значения для валидации
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if suffix == ".json":
        with open(path, encoding="utf-8") as file:
            return pd.DataFrame(json.load(file))
    raise ValueError(f"Неподдерживаемый формат файла: {path.suffix}")


def parse_date(value):
    """Разбирает дату по известным форматам или возвращает None."""
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(str(value).strip(), date_format)
        except ValueError:
            continue
    return None
