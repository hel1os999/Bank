import logging
from typing import Optional, TYPE_CHECKING

from fastapi_users import (
    BaseUserManager,
    IntegerIDMixin,
)

from core.config import settings
from core.email import send_password_reset_email, send_verification_email
from core.types.user_id import UserIdType
from core.models import User

if TYPE_CHECKING:
    from fastapi import Request

log = logging.getLogger(__name__)


class UserManager(IntegerIDMixin, BaseUserManager[User, UserIdType]):
    reset_password_token_secret = settings.access_token.reset_password_token_secret
    verification_token_secret = settings.access_token.verification_token_secret

    async def on_after_register(
        self,
        user: User,
        request: Optional["Request"] = None,
    ):
        log.info("New registration: user_id=%s email=%s", user.id, user.email)
        # Automatically dispatch the verification email so the user does not
        # have to request it manually after registering.
        await self.request_verify(user, request)

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.info("Verification token issued: user_id=%s", user.id)
        await send_verification_email(to=user.email, token=token)

    async def on_after_verify(
        self,
        user: User,
        request: Optional["Request"] = None,
    ):
        log.info("Email verified: user_id=%s email=%s", user.id, user.email)

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.info("Password reset requested: user_id=%s", user.id)
        await send_password_reset_email(to=user.email, token=token)

    async def on_after_reset_password(
        self,
        user: User,
        request: Optional["Request"] = None,
    ):
        log.info("Password reset completed: user_id=%s", user.id)
