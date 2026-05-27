from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.catalog import get_onboarding_steps
from core.models import User, bank_db_helper, userdata_db_helper
from core.schemas.onboarding import OnboardingRead, OnboardingStepRead
from crud.onboarding import get_onboarding_progress

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)


@router.get("", response_model=OnboardingRead)
async def get_onboarding(
    user_session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    bank_session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_onboarding_progress(
        user_session=user_session,
        bank_session=bank_session,
        user=user,
    )


@router.get("/steps", response_model=list[OnboardingStepRead])
async def get_onboarding_steps_catalog():
    return [
        {**step, "completed": False, "status": "PENDING"}
        for step in get_onboarding_steps()
    ]
