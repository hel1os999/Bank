from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import Work, WorkExperience
from core.models import UserDataBase

if TYPE_CHECKING:
    from core.models import UserDocument


class UserSurvey(UserDataBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    user_document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    residential_address: Mapped[str]
    work: Mapped[Work] = mapped_column(
        Enum(Work), default=Work.UNEMPLOYED, nullable=False
    )
    work_experience: Mapped[WorkExperience] = mapped_column(
        Enum(WorkExperience), default=WorkExperience.LACK_OF_EXPERIENCE, nullable=False
    )
    salary: Mapped[str]
    additional_income: Mapped[str] = mapped_column(nullable=True)
    work_address: Mapped[str] = mapped_column(nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    document: Mapped["UserDocument"] = relationship(
        "UserDocument", back_populates="surveys"
    )
