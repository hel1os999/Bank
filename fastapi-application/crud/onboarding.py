from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.catalog import get_onboarding_steps
from core.models import Account, Card, User, UserDocument, UserSurvey


async def get_onboarding_progress(
    user_session: AsyncSession,
    bank_session: AsyncSession,
    user: User,
) -> dict:
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

    accounts_count = (
        await bank_session.scalar(
            select(func.count(Account.id)).where(Account.user_id == user.id)
        )
        or 0
    )
    cards_count = (
        await bank_session.scalar(
            select(func.count(Card.id)).join(Account).where(Account.user_id == user.id)
        )
        or 0
    )

    completed_map = {
        "verify_email": bool(user.is_verified),
        "submit_documents": bool(document),
        "complete_survey": bool(survey),
        "open_account": accounts_count > 0,
        "issue_card": cards_count > 0,
    }

    steps = []
    for step in get_onboarding_steps():
        completed = completed_map[step["code"]]
        steps.append(
            {
                **step,
                "completed": completed,
                "status": "COMPLETED" if completed else "PENDING",
            }
        )

    required_steps = [step for step in steps if step["required"]]
    completed_required = sum(1 for step in required_steps if step["completed"])
    progress_percent = int((completed_required / len(required_steps)) * 100)
    next_step = next(
        (step["code"] for step in steps if step["required"] and not step["completed"]),
        None,
    )
    document_status = document.verification_status if document else None
    survey_status = survey.verification_status if survey else None
    kyc_status = (
        "APPROVED"
        if document_status == "APPROVED" and survey_status == "APPROVED"
        else "PENDING"
    )

    return {
        "user_id": user.id,
        "kyc_status": kyc_status,
        "progress_percent": progress_percent,
        "next_step": next_step,
        "steps": steps,
    }
