from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from core.crypto import decrypt_data, encrypt_data


MONEY_QUANT = Decimal("0.01")


def normalize_money(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def encrypt_money(value: Decimal | int | str) -> str:
    return encrypt_data(str(normalize_money(value)))


def decrypt_money(value: str) -> Decimal:
    return normalize_money(decrypt_data(value))


def decrypt_optional_money(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return decrypt_money(value)


def enum_value(value) -> str:
    return getattr(value, "value", value)


def mask_pan(last_four: str) -> str:
    return f"**** **** **** {last_four}"


def now_utc_naive() -> datetime:
    return datetime.utcnow()
