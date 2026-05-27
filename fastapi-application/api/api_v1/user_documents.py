from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.models import User, userdata_db_helper
from core.schemas.user_document import UserDocumentRead, UserDocumentCreate
from crud.user_documents import create_user_document, get_document_by_id, get_documents

router = APIRouter(
    prefix=settings.api.v1.documents,
    tags=["User_Documents"],
)


@router.post("", response_model=UserDocumentRead, status_code=status.HTTP_201_CREATED)
async def create_user_documents(
    user_document: UserDocumentCreate,
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_user_document(
        user_document=user_document, session=session, user=user
    )


@router.get("/{document_id}", response_model=UserDocumentRead)
async def get_user_documents_by_id(
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    document_id: int,
    user: User = Depends(current_active_user),
):
    return await get_document_by_id(session=session, document_id=document_id, user=user)


@router.get("", response_model=list[UserDocumentRead])
async def get_user_document(
    session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_documents(session=session, user=user)
