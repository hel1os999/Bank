from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money, enum_value
from core.crypto import decrypt_data, encrypt_data
from core.models import User, UserSurvey, UserDocument
from core.schemas.user_survey import UserSurveyCreate


async def create_survey(
    session: AsyncSession, user_survey: UserSurveyCreate, user: User
):
    stmt = select(UserDocument).where(UserDocument.user_id == user.id)
    result = await session.execute(stmt)
    document = result.unique().scalars().first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Create a document before submitting a survey",
        )

    new_user_survey = UserSurvey(
        user_document_id=document.id,
        residential_address=encrypt_data(user_survey.residential_address),
        work=enum_value(user_survey.work),
        work_experience=enum_value(user_survey.work_experience),
        salary=encrypt_money(user_survey.salary),
        additional_income=encrypt_money(user_survey.additional_income or 0),
        work_address=encrypt_data(user_survey.work_address),
        verification_status="PENDING",
    )
    session.add(new_user_survey)
    await session.commit()
    await session.refresh(new_user_survey)

    return serialize_survey(new_user_survey)


async def get_survey_by_id(session: AsyncSession, survey_id: int, user: User):
    stmt = (
        select(UserSurvey)
        .join(UserDocument)
        .where(
            UserSurvey.id == survey_id,
            UserDocument.user_id == user.id,
        )
    )
    result = await session.execute(stmt)
    survey = result.scalars().first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
        )
    return serialize_survey(survey)


async def get_surveys(session: AsyncSession, user: User):
    stmt = select(UserSurvey).join(UserDocument).where(UserDocument.user_id == user.id)
    result = await session.execute(stmt)
    return [serialize_survey(survey) for survey in result.scalars().all()]


def serialize_survey(survey: UserSurvey) -> dict:
    return {
        "id": survey.id,
        "user_document_id": survey.user_document_id,
        "residential_address": decrypt_data(survey.residential_address),
        "work": survey.work,
        "work_experience": survey.work_experience,
        "salary": decrypt_money(survey.salary),
        "additional_income": (
            decrypt_money(survey.additional_income)
            if survey.additional_income
            else None
        ),
        "work_address": (
            decrypt_data(survey.work_address) if survey.work_address else None
        ),
        "verification_status": survey.verification_status,
    }
