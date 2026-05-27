from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Integer, ForeignKey, String, text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from core.models import UserDataBase

if TYPE_CHECKING:
    from core.models import User, UserSurvey


class UserDocument(UserDataBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="cascade"),
        nullable=False,
    )
    data: Mapped[str]
    passport_number: Mapped[str] = mapped_column(
        String, unique=True
    )  # only for users search
    updated_at: Mapped[datetime]
    verification_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    user: Mapped["User"] = relationship("User", back_populates="documents")
    # Allows document.surveys
    surveys: Mapped["UserSurvey"] = relationship(
        "UserSurvey", back_populates="document"
    )
