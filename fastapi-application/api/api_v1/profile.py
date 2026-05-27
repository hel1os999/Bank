from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.models import (
    Account,
    Card,
    User,
    UserDocument,
    UserSurvey,
    bank_db_helper,
    userdata_db_helper,
)
from core.schemas.profile import CustomerProfileRead

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.get("", response_model=CustomerProfileRead)
async def get_profile(
    user_session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    bank_session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    document_result = await user_session.execute(
        select(UserDocument)
        .where(UserDocument.user_id == user.id)
        .order_by(UserDocument.updated_at.desc())
    )
    document = document_result.scalars().first()

    survey = None
    if document:
        survey_result = await user_session.execute(
            select(UserSurvey)
            .where(UserSurvey.user_document_id == document.id)
            .order_by(UserSurvey.id.desc())
        )
        survey = survey_result.scalars().first()

    accounts_count = await bank_session.scalar(
        select(func.count(Account.id)).where(Account.user_id == user.id)
    )
    cards_count = await bank_session.scalar(
        select(func.count(Card.id)).join(Account).where(Account.user_id == user.id)
    )
    document_status = document.verification_status if document else None
    survey_status = survey.verification_status if survey else None
    kyc_status = (
        "APPROVED"
        if document_status == "APPROVED" and survey_status == "APPROVED"
        else "PENDING"
    )
    available_products = ["accounts", "cards"]
    if kyc_status == "APPROVED":
        available_products.extend(["payments", "beneficiaries", "credits", "deposits"])

    return {
        "user_id": user.id,
        "email": user.email,
        "document_status": document_status,
        "survey_status": survey_status,
        "kyc_status": kyc_status,
        "accounts_count": accounts_count or 0,
        "cards_count": cards_count or 0,
        "available_products": available_products,
    }
