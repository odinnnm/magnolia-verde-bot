import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    editor = "editor"
    admin = "admin"


class PostStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    published = "published"
    archived = "archived"
    failed = "failed"


USER_ROLE_ENUM = PgEnum(UserRole, name="user_role", create_type=False)
POST_STATUS_ENUM = PgEnum(PostStatus, name="post_status", create_type=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        USER_ROLE_ENUM,
        default=UserRole.editor,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    settings_updates: Mapped[list["BotSetting"]] = relationship(back_populates="updated_by_user")


class Channel(TimestampMixin, Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="channel")


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("channels.id", ondelete="SET NULL"), index=True)
    status: Mapped[PostStatus] = mapped_column(
        POST_STATUS_ENUM,
        default=PostStatus.draft,
        nullable=False,
        index=True,
    )
    object_type: Mapped[str | None] = mapped_column(String(100))
    source_photo_file_id: Mapped[str | None] = mapped_column(String(255))
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    price_text: Mapped[str | None] = mapped_column(String(255))
    availability_text: Mapped[str | None] = mapped_column(String(255))
    story_text: Mapped[str | None] = mapped_column(Text)
    colors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    style_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    published_message_id: Mapped[int | None] = mapped_column(BigInteger)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_reason: Mapped[str | None] = mapped_column(Text)

    author: Mapped["User"] = relationship(back_populates="posts")
    channel: Mapped["Channel | None"] = relationship(back_populates="posts")
    images: Mapped[list["PostImage"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    flower_matches: Mapped[list["PostFlowerMatch"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class PostImage(TimestampMixin, Base):
    __tablename__ = "post_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_file_unique_id: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    post: Mapped["Post"] = relationship(back_populates="images")


class FlowerDictionary(TimestampMixin, Base):
    __tablename__ = "flower_dictionary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    post_matches: Mapped[list["PostFlowerMatch"]] = relationship(back_populates="flower")


class PostFlowerMatch(TimestampMixin, Base):
    __tablename__ = "post_flower_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    flower_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flower_dictionary.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    source_name: Mapped[str | None] = mapped_column(String(255))

    post: Mapped["Post"] = relationship(back_populates="flower_matches")
    flower: Mapped["FlowerDictionary"] = relationship(back_populates="post_matches")


class BotSetting(TimestampMixin, Base):
    __tablename__ = "bot_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    updated_by_user: Mapped["User | None"] = relationship(back_populates="settings_updates")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")
