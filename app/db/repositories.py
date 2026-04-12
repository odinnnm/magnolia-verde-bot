from datetime import datetime, timezone

from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Draft, DraftStatus
from app.schemas.draft import DraftPost


class DraftRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save_draft(self, user_id: int, draft: DraftPost, status: str = "draft") -> Draft:
        draft_status = DraftStatus(status)
        async with self.session_factory() as session:
            record = Draft(
                user_id=user_id,
                status=draft_status,
                photo_file_id=draft.photo_file_id,
                object_type=draft.object_type,
                flowers=draft.flowers,
                colors=draft.colors,
                style_tags=draft.style_tags,
                caption=draft.caption,
                price_text=draft.price_text,
                availability_text=draft.availability_text,
                story_text=draft.story_text,
                published_at=datetime.now(timezone.utc) if draft_status is DraftStatus.published else None,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def list_user_drafts(self, user_id: int, limit: int = 5) -> Sequence[Draft]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Draft)
                .where(Draft.user_id == user_id)
                .order_by(desc(Draft.created_at))
                .limit(limit)
            )
            return result.scalars().all()
