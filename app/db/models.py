import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DraftStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Draft(TimestampMixin, Base):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus, name="draft_status"),
        default=DraftStatus.draft,
        nullable=False,
    )
    photo_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(100))
    flowers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    colors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    style_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    price_text: Mapped[str | None] = mapped_column(String(255))
    availability_text: Mapped[str | None] = mapped_column(String(255))
    story_text: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
