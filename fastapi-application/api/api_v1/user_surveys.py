from fastapi import APIRouter, Depends
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.models import userdata_db_helper, User
from core.schemas.user_survey import UserSurveyCreate, UserSurveyRead
from crud.user_surveys import create_survey, get_survey_by_id, get_surveys

router = APIRouter(
    prefix=settings.api.v1.user_survey,
    tags=["/User_Surveys"],
)


@router.post("", response_model=UserSurveyRead)
async def create_user_surveys(
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    user_survey: UserSurveyCreate,
    user: User = Depends(current_active_user),
):
    return await create_survey(session=session, user_survey=user_survey, user=user)


@router.get("", response_model=list[UserSurveyRead])
async def list_surveys(
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_surveys(session=session, user=user)


@router.get("/{survey_id}", response_model=UserSurveyRead)
async def get_surveys_by_id(
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    survey_id: int,
    user: User = Depends(current_active_user),
):
    return await get_survey_by_id(session=session, survey_id=survey_id, user=user)
