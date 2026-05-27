from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_superuser
from core.models import User, UserDocument, UserSurvey, userdata_db_helper

router = APIRouter(prefix="/admin", tags=["Admin"])


class VerificationUpdate(BaseModel):
    status: str  # APPROVED | REJECTED | PENDING


@router.patch("/documents/{document_id}/verify")
async def verify_document(
    document_id: int,
    payload: VerificationUpdate,
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    _: User = Depends(current_active_superuser),
):
    result = await session.execute(
        select(UserDocument).where(UserDocument.id == document_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.verification_status = payload.status
    await session.commit()
    return {"document_id": document_id, "verification_status": document.verification_status}


@router.patch("/surveys/{survey_id}/verify")
async def verify_survey(
    survey_id: int,
    payload: VerificationUpdate,
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    _: User = Depends(current_active_superuser),
):
    result = await session.execute(
        select(UserSurvey).where(UserSurvey.id == survey_id)
    )
    survey = result.scalars().first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    survey.verification_status = payload.status
    await session.commit()
    return {"survey_id": survey_id, "verification_status": survey.verification_status}
