"""Константы предметной области: типы операций и статусы."""

# Типы операций
DEPOSIT = "deposit"
WITHDRAW = "withdraw"
INTEREST = "interest"
KNOWN_OPERATIONS = (DEPOSIT, WITHDRAW, INTEREST)

# Статусы операций
SUCCESS = "success"
FAIL = "fail"
KNOWN_STATUSES = (SUCCESS, FAIL)

# Источники записей истории
SOURCE_MANUAL = "manual"
SOURCE_TRANSFER = "transfer"
SOURCE_IMPORT = "import"
