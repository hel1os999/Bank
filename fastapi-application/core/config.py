from pydantic import BaseModel
from pydantic import PostgresDsn
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    auth: str = "/auth"
    users: str = "/users"
    messages: str = "/messages"
    documents: str = "/documents"
    user_survey: str = "/user-surveys"
    accounts: str = "/accounts"
    cards: str = "/cards"
    transactions: str = "/transactions"
    beneficiaries: str = "/beneficiaries"
    payments: str = "/payments"
    ledger: str = "/ledger"
    products: str = "/products"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()

    @property
    def bearer_token_url(self) -> str:
        # api/v1/auth/login
        parts = (self.prefix, self.v1.prefix, self.v1.auth, "/login")
        path = "".join(parts)
        # return path[1:]
        return path.removeprefix("/")


class DatabaseConfig(BaseModel):
    userdata_url: PostgresDsn
    bank_url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class SmtpConfig(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    from_address: str = ""
    use_tls: bool = True
    enabled: bool = False


class RedisDb(BaseModel):
    cache: int = 0


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: RedisDb = RedisDb()


class CacheNamespaces(BaseModel):
    accounts_list: str = "accounts_list"
    accounts_detail: str = "accounts_detail"
    cards_list: str = "cards_list"
    cards_detail: str = "cards_detail"
    transactions_list: str = "transactions_list"
    payments_list: str = "payments_list"
    ledger_list: str = "ledger_list"
    beneficiaries_list: str = "beneficiaries_list"
    credits_list: str = "credits_list"
    deposits_list: str = "deposits_list"


class CacheConfig(BaseModel):
    prefix: str = "bank"
    expire_accounts: int = 5
    expire_transactions: int = 10
    expire_payments: int = 10
    expire_ledger: int = 10
    expire_cards: int = 15
    expire_beneficiaries: int = 30
    expire_credits: int = 30
    expire_deposits: int = 30
    namespace: CacheNamespaces = CacheNamespaces()


class RabbitMQConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 5672
    password: str
    user: str
    exchange: str
    payments_routing_key: str = "payments"
    transactions_routing_key: str = "transactions"
    documents_routing_key: str | None = None
    surveys_routing_key: str
    rmq_url: str


class VariableForCard(BaseModel):
    chase_bin: int = 400011  # Chase, Visa, Credit, USA
    sparkasse_bin: int = 502102  # Sparkasse, Mastercard, Debit, DE


class AccessToken(BaseModel):
    lifetime_seconds: int = 3600
    reset_password_token_secret: str
    verification_token_secret: str


class Cryptography(BaseModel):
    db_encryption_key: str
    passport_hash_salt: str
    card_hash_salt: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()
    db: DatabaseConfig
    access_token: AccessToken
    cryptography: Cryptography
    card_variable: VariableForCard = VariableForCard()
    rmq: RabbitMQConfig
    redis: RedisConfig = RedisConfig()
    cache: CacheConfig = CacheConfig()
    smtp: SmtpConfig = SmtpConfig()


settings = Settings()
