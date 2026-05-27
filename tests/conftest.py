"""
Test environment bootstrap.

Sets fake APP_CONFIG__ env vars BEFORE any test module imports core.config,
so that Settings() can be instantiated without a real .env file.

All values are intentionally fake — safe to commit to VCS.
The Fernet key is 32 zero-bytes in URL-safe base64, valid but useless outside tests.
"""

import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "fastapi-application"
sys.path.insert(0, str(APP_ROOT))

_TEST_ENV = {
    # Postgres (not actually connected in unit tests)
    "APP_CONFIG__DB__USERDATA_URL": "postgresql+asyncpg://user:password@localhost:5432/userdata",
    "APP_CONFIG__DB__BANK_URL":     "postgresql+asyncpg://manager:pwd@localhost:5432/bank",

    # JWT secrets
    "APP_CONFIG__ACCESS_TOKEN__RESET_PASSWORD_TOKEN_SECRET": "test-reset-secret-for-unit-tests-only",
    "APP_CONFIG__ACCESS_TOKEN__VERIFICATION_TOKEN_SECRET":   "test-verify-secret-for-unit-tests-only",

    # Fernet key — 32 zero-bytes in URL-safe base64, valid format, useless in prod
    "APP_CONFIG__CRYPTOGRAPHY__DB_ENCRYPTION_KEY": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "APP_CONFIG__CRYPTOGRAPHY__PASSPORT_HASH_SALT": "test-passport-salt",
    "APP_CONFIG__CRYPTOGRAPHY__CARD_HASH_SALT":     "test-card-salt",

    # RabbitMQ (not actually connected in unit tests)
    "APP_CONFIG__RMQ__USER":                "test-user",
    "APP_CONFIG__RMQ__PASSWORD":            "test-password",
    "APP_CONFIG__RMQ__EXCHANGE":            "test-exchange",
    "APP_CONFIG__RMQ__SURVEYS_ROUTING_KEY": "surveys",
    "APP_CONFIG__RMQ__RMQ_URL":             "amqp://test:test@localhost:5672/",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)
