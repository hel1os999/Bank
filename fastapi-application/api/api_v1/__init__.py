from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.security import HTTPBearer

from core.config import settings

from .auth import router as auth_router
from .health import router as health_router
from .users import router as users_router
from .user_documents import router as user_documents_router
from .user_surveys import router as user_surveys_router
from .accounts import router as accounts_router
from .cards import router as cards_router
from .transactions import router as transactions_router
from .profile import router as profile_router
from .beneficiaries import router as beneficiaries_router
from .payments import router as payments_router
from .ledger import router as ledger_router
from .products import router as products_router
from .onboarding import router as onboarding_router
from .admin import router as admin_router

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix=settings.api.v1.prefix,
    dependencies=[Depends(http_bearer)],
)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(user_documents_router)
router.include_router(user_surveys_router)
router.include_router(accounts_router)
router.include_router(cards_router)
router.include_router(transactions_router)
router.include_router(profile_router)
router.include_router(beneficiaries_router)
router.include_router(payments_router)
router.include_router(ledger_router)
router.include_router(products_router)
router.include_router(onboarding_router)
router.include_router(admin_router)
