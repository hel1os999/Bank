from functools import lru_cache


@lru_cache(maxsize=1)
def get_product_catalog() -> tuple[dict, ...]:
    return (
        {
            "code": "debit_account",
            "name": "Everyday account",
            "description": "Main account for salary, cards, transfers, and payments.",
            "category": "accounts",
            "requires_kyc": True,
        },
        {
            "code": "virtual_card",
            "name": "Virtual card",
            "description": "Instant card for online payments with freeze and reveal controls.",
            "category": "cards",
            "requires_kyc": True,
        },
        {
            "code": "internal_payments",
            "name": "Payments",
            "description": "Transfers with beneficiaries, idempotency, statuses, and ledger history.",
            "category": "payments",
            "requires_kyc": True,
        },
        {
            "code": "savings_deposit",
            "name": "Savings deposit",
            "description": "Term deposit product with rate, maturity date, and active status.",
            "category": "deposits",
            "requires_kyc": True,
        },
        {
            "code": "consumer_credit",
            "name": "Consumer credit",
            "description": "Credit product with principal, outstanding balance, and next payment date.",
            "category": "credits",
            "requires_kyc": True,
        },
    )


@lru_cache(maxsize=1)
def get_onboarding_steps() -> tuple[dict, ...]:
    return (
        {
            "code": "verify_email",
            "title": "Verify email",
            "description": "Confirm the account email before using banking products.",
            "required": True,
        },
        {
            "code": "submit_documents",
            "title": "Submit documents",
            "description": "Upload identity data for KYC review.",
            "required": True,
        },
        {
            "code": "complete_survey",
            "title": "Complete customer survey",
            "description": "Provide address, work, and income information.",
            "required": True,
        },
        {
            "code": "open_account",
            "title": "Open first account",
            "description": "Create an account after the profile data is ready.",
            "required": True,
        },
        {
            "code": "issue_card",
            "title": "Issue first card",
            "description": "Create a card linked to an owned account.",
            "required": False,
        },
    )
