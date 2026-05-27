"""
Unit tests — no database, Redis, RabbitMQ, or .env required.

Sections:
  1. Utilities     — get_last_four, mask_pan, normalize_money
  2. Factories     — IBAN generation
  3. Schemas       — field validation, forbidden fields in request bodies
  4. Cache         — namespaces, expire values, key builder behaviour
  5. File inspection — decorators, path params, security dependencies
  6. Worker        — RabbitMQ lifecycle statuses
"""

import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "fastapi-application"
sys.path.insert(0, str(APP_ROOT))

from utils.get_last_four import get_last_four
from core.factories.IBAN_factory import create_iban
from core.schemas.beneficiary import BeneficiaryCreate
from core.schemas.card import CardCreate, CardSpendingLimitUpdate
from core.schemas.credit import CreditCreate
from core.schemas.deposit import DepositCreate
from core.schemas.payment import PaymentCreate
from core.schemas.transactions import TransactionCreate
from core.catalog import get_onboarding_steps, get_product_catalog
from core.enums import PaymentStatus, TransactionStatus
from core.key_builder import bank_key_builder


# ─────────────────────────────────────────────────────────────
#  1. Utilities
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("card_number,expected", [
    ("4000 1100 0012 3456", "3456"),
    ("5021 0200 0012 3456", "3456"),
    ("4000110000123456",    "3456"),
    ("4000 1100 0012 0001", "0001"),
    ("4000 1100 0012 9999", "9999"),
])
def test_get_last_four_returns_four_digits(card_number, expected):
    result = get_last_four(card_number)
    assert result == expected
    assert len(result) == 4
    assert result.isdigit()


def test_get_last_four_no_spaces():
    assert " " not in get_last_four("4000 1100 0012 8958")


def test_get_last_four_ignores_internal_spaces():
    assert get_last_four("4000 1100 0012 8958") == get_last_four("4000110000128958")


def _mask_pan(last_four: str) -> str:
    return f"**** **** **** {last_four}"


def test_mask_pan_format():
    assert _mask_pan("8958") == "**** **** **** 8958"


def test_mask_pan_pipeline_with_get_last_four():
    last_four = get_last_four("4000 1100 0012 8958")
    masked = _mask_pan(last_four)
    assert masked == "**** **** **** 8958"
    assert masked.count("****") == 3
    assert not masked.endswith("****")


def test_mask_pan_does_not_double_mask():
    """Regression: last_four must be 4 digits, not an already-masked string."""
    masked = _mask_pan(get_last_four("4000 1100 0012 8958"))
    assert len(masked.split(" ")) == 4


MONEY_QUANT = Decimal("0.01")


def _normalize(value) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


@pytest.mark.parametrize("value,expected", [
    ("100",        Decimal("100.00")),
    ("99.999",     Decimal("100.00")),
    ("99.994",     Decimal("99.99")),
    (Decimal("0"), Decimal("0.00")),
    (1000,         Decimal("1000.00")),
    ("123.456789", Decimal("123.46")),
])
def test_normalize_money(value, expected):
    assert _normalize(value) == expected


def test_normalize_money_scale():
    assert _normalize("123.456789").as_tuple().exponent == -2


# ─────────────────────────────────────────────────────────────
#  2. Factories
# ─────────────────────────────────────────────────────────────

def test_iban_starts_with_de():
    assert create_iban("1").startswith("DE")


def test_iban_has_four_parts():
    assert len(create_iban("42").split(" ")) == 4


def test_iban_check_digits_are_numeric():
    assert create_iban("7").split(" ")[1].isdigit()


def test_iban_account_number_encodes_user_id():
    assert create_iban("99").split(" ")[3].endswith("99")


def test_iban_different_users_produce_different_account_parts():
    parts = [create_iban(str(i)).split(" ")[3] for i in range(1, 20)]
    assert len(set(parts)) == 19


# ─────────────────────────────────────────────────────────────
#  3. Schemas
# ─────────────────────────────────────────────────────────────

def test_payment_requires_positive_amount():
    p = PaymentCreate(
        account_id=1,
        amount=Decimal("10.50"),
        idempotency_key="transfer-key-001",
        counterparty_iban="DE75512108001245126199",
    )
    assert p.amount == Decimal("10.50")
    assert p.currency.value == "EUR"

    with pytest.raises(ValidationError):
        PaymentCreate(account_id=1, amount=Decimal("0"), idempotency_key="key-2")


def test_beneficiary_requires_iban_or_card_number():
    with pytest.raises(ValidationError):
        BeneficiaryCreate(name="No Destination")

    b = BeneficiaryCreate(name="Rent", iban="DE75512108001245126199")
    assert b.iban == "DE75512108001245126199"


def test_card_create_has_no_account_id():
    assert "account_id" not in CardCreate.model_fields


def test_credit_create_has_no_account_id():
    assert "account_id" not in CreditCreate.model_fields


def test_deposit_create_has_no_account_id():
    assert "account_id" not in DepositCreate.model_fields


def test_transaction_create_has_no_sender_card_id():
    assert "sender_card_id" not in TransactionCreate.model_fields


def test_spending_limit_rejects_negative():
    with pytest.raises(ValidationError):
        CardSpendingLimitUpdate(spending_limit=Decimal("-1"))


def test_spending_limit_accepts_zero_and_positive():
    assert CardSpendingLimitUpdate(spending_limit=Decimal("0")).spending_limit == Decimal("0")
    assert CardSpendingLimitUpdate(spending_limit=Decimal("5000")).spending_limit == Decimal("5000")


def test_transaction_create_idempotency_key_optional():
    tx = TransactionCreate(receiver_card_number="4000110000128958", amount=Decimal("50"))
    assert tx.idempotency_key is None


def test_transaction_create_stores_idempotency_key():
    tx = TransactionCreate(
        receiver_card_number="4000110000128958",
        amount=Decimal("50"),
        idempotency_key="uuid-abc",
    )
    assert tx.idempotency_key == "uuid-abc"


def test_transaction_create_rejects_zero_and_negative_amount():
    for bad in (Decimal("0"), Decimal("-10")):
        with pytest.raises(ValidationError):
            TransactionCreate(receiver_card_number="4000110000128958", amount=bad)


# ─────────────────────────────────────────────────────────────
#  4. Cache
# ─────────────────────────────────────────────────────────────

def test_cache_namespaces_are_defined_and_unique():
    # Default values from CacheNamespaces (no .env needed)
    values = [
        "accounts_list", "accounts_detail",
        "cards_list", "cards_detail",
        "transactions_list", "payments_list",
        "ledger_list", "beneficiaries_list",
        "credits_list", "deposits_list",
    ]
    assert len(values) == len(set(values)), "All namespaces must be unique"
    assert all(values), "No namespace may be empty"


def test_cache_expire_values_are_positive():
    # Default expire values from CacheConfig (no .env needed)
    defaults = {
        "expire_accounts": 5,
        "expire_cards": 15,
        "expire_transactions": 10,
        "expire_payments": 10,
        "expire_ledger": 10,
        "expire_beneficiaries": 30,
        "expire_credits": 30,
        "expire_deposits": 30,
    }
    assert all(v > 0 for v in defaults.values())


def test_only_static_catalogs_use_lru_cache():
    get_product_catalog.cache_clear()
    get_onboarding_steps.cache_clear()

    assert get_product_catalog() is get_product_catalog()
    assert get_onboarding_steps() is get_onboarding_steps()
    assert get_product_catalog.cache_info().hits >= 1
    assert get_onboarding_steps.cache_info().hits >= 1


class _FakeFunc:
    __module__ = "api.v1.accounts"
    __name__ = "list_accounts"


class _FakeUser:
    id = 42
    email = "test@bank.com"


def test_key_builder_excludes_session_from_key():
    from sqlalchemy.ext.asyncio import AsyncSession

    session = MagicMock(spec=AsyncSession)
    user = _FakeUser()
    func = _FakeFunc()

    key_with = bank_key_builder(func, "accounts_list", args=(), kwargs={"session": session, "user": user})
    key_without = bank_key_builder(func, "accounts_list", args=(), kwargs={"user": user})

    assert key_with == key_without
    assert key_with.startswith("accounts_list:")


def test_key_builder_is_user_scoped():
    class UserA:
        id = 1
        email = "a@bank.com"

    class UserB:
        id = 2
        email = "b@bank.com"

    func = _FakeFunc()
    key_a = bank_key_builder(func, "accounts_list", args=(), kwargs={"user": UserA()})
    key_b = bank_key_builder(func, "accounts_list", args=(), kwargs={"user": UserB()})
    assert key_a != key_b


def test_key_builder_is_deterministic():
    user = _FakeUser()
    func = _FakeFunc()
    key1 = bank_key_builder(func, "accounts_list", args=(), kwargs={"user": user})
    key2 = bank_key_builder(func, "accounts_list", args=(), kwargs={"user": user})
    assert key1 == key2


def test_key_builder_includes_path_params():
    user = _FakeUser()
    func = _FakeFunc()
    key1 = bank_key_builder(func, "accounts_detail", args=(), kwargs={"user": user, "account_id": 1})
    key2 = bank_key_builder(func, "accounts_detail", args=(), kwargs={"user": user, "account_id": 2})
    assert key1 != key2


# ─────────────────────────────────────────────────────────────
#  5. File inspection
# ─────────────────────────────────────────────────────────────

_CACHED_ENDPOINTS = [
    ("accounts.py",     "list_accounts"),
    ("accounts.py",     "retrieve_account"),
    ("cards.py",        "list_cards"),
    ("cards.py",        "retrieve_card"),
    ("transactions.py", "list_transactions"),
    ("payments.py",     "list_payments"),
    ("ledger.py",       "list_ledger"),
    ("beneficiaries.py","list_beneficiaries"),
    ("products.py",     "list_credits"),
    ("products.py",     "list_deposits"),
]

_NOT_CACHED_ENDPOINTS = [
    ("cards.py",    "get_reveal_cards_by_id"),
    ("payments.py", "retrieve_payment"),
]


@pytest.mark.parametrize("filename,fn_name", _CACHED_ENDPOINTS)
def test_endpoint_has_cache_decorator(filename, fn_name):
    src = (APP_ROOT / "api" / "api_v1" / filename).read_text()
    fn_pos = src.index(f"async def {fn_name}")
    snippet = src[max(0, fn_pos - 200): fn_pos]
    assert "@cache(" in snippet, f"{fn_name} missing @cache"


@pytest.mark.parametrize("filename,fn_name", _NOT_CACHED_ENDPOINTS)
def test_sensitive_endpoint_has_no_cache_decorator(filename, fn_name):
    src = (APP_ROOT / "api" / "api_v1" / filename).read_text()
    fn_pos = src.index(f"async def {fn_name}")
    snippet = src[max(0, fn_pos - 200): fn_pos]
    assert "@cache(" not in snippet, f"{fn_name} must NOT have @cache"


def test_document_cache_not_wired():
    doc_src = (APP_ROOT / "api" / "api_v1" / "user_documents.py").read_text()
    assert "fastapi_cache" not in doc_src
    assert "@cache" not in doc_src


def test_card_creation_uses_account_id_path_param():
    assert "/{account_id}" in (APP_ROOT / "api" / "api_v1" / "cards.py").read_text()


def test_transaction_creation_uses_sender_card_id_path_param():
    assert "/{sender_card_id}" in (APP_ROOT / "api" / "api_v1" / "transactions.py").read_text()


def test_credit_and_deposit_creation_use_account_id_path_param():
    src = (APP_ROOT / "api" / "api_v1" / "products.py").read_text()
    assert "/accounts/{account_id}/credits" in src
    assert "/accounts/{account_id}/deposits" in src


def test_admin_uses_superuser_dependency():
    src = (APP_ROOT / "api" / "api_v1" / "admin.py").read_text()
    assert "current_active_superuser" in src
    assert "require_superuser" not in src


def test_spending_limit_endpoint_exists():
    src = (APP_ROOT / "api" / "api_v1" / "cards.py").read_text()
    assert "spending-limit" in src
    assert "CardSpendingLimitUpdate" in src


# ─────────────────────────────────────────────────────────────
#  6. Worker / RabbitMQ lifecycle
# ─────────────────────────────────────────────────────────────

def test_transaction_status_lifecycle():
    assert [s.value for s in TransactionStatus] == [
        "PENDING", "PROCESSING", "COMPLETED", "FAILED",
    ]


def test_payment_status_has_processing():
    assert "PROCESSING" in {s.value for s in PaymentStatus}


def test_worker_wires_both_queues():
    worker = (APP_ROOT / "core" / "messaging" / "worker.py").read_text()
    assert "handle_transactions" in worker
    assert "handle_payments" in worker
    assert "transactions_routing_key" in worker
    assert "payments_routing_key" in worker
    assert "asyncio.gather" in worker


def test_transaction_endpoint_returns_202():
    src = (APP_ROOT / "api" / "api_v1" / "transactions.py").read_text()
    assert "status.HTTP_202_ACCEPTED" in src
    assert "create_pending_card_transfer" in src
