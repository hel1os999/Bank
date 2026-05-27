from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt_data, generate_passport_search_hash, decrypt_data
from core.models import User
from core.models.user_document import UserDocument
from core.schemas.user_document import UserDocumentCreate


async def create_user_document(
    user_document: UserDocumentCreate,
    session: AsyncSession,
    user: User,
):

    encrypted_data = encrypt_data(user_document.data)
    passport_hash = generate_passport_search_hash(user_document.passport_number)

    new_document = UserDocument(
        user_id=user.id,
        passport_number=passport_hash,
        data=encrypted_data,
        updated_at=datetime.now(),
        verification_status="PENDING",
    )

    session.add(new_document)
    await session.commit()

    await session.refresh(new_document)
    return serialize_document(new_document)


async def get_document_by_id(session: AsyncSession, document_id: int, user: User):
    stmt = select(UserDocument).where(
        UserDocument.id == document_id, UserDocument.user_id == user.id
    )
    result = await session.execute(stmt)
    data = result.scalars().first()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return serialize_document(data)


async def get_documents(session: AsyncSession, user: User):
    stmt = (
        select(UserDocument)
        .where(UserDocument.user_id == user.id)
        .order_by(UserDocument.updated_at.desc())
    )
    result = await session.execute(stmt)
    return [serialize_document(document) for document in result.scalars().all()]


def serialize_document(document: UserDocument) -> dict:
    return {
        "id": document.id,
        "user_id": document.user_id,
        "data": decrypt_data(document.data),
        "passport_number": document.passport_number,
        "updated_at": document.updated_at,
        "verification_status": document.verification_status,
    }
