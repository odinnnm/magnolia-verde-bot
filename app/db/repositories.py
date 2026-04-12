from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Channel, Post, PostImage, PostStatus, User
from app.schemas.draft import DraftPost


class UserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_user_id == telegram_user_id)
            )
            return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_user_id == telegram_user_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                user = User(
                    telegram_user_id=telegram_user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user

            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()
            await session.refresh(user)
            return user


class ChannelRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Channel | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Channel).where(Channel.telegram_chat_id == telegram_chat_id)
            )
            return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_chat_id: int,
        title: str,
        username: str | None = None,
        is_default: bool = False,
    ) -> Channel:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Channel).where(Channel.telegram_chat_id == telegram_chat_id)
            )
            channel = result.scalar_one_or_none()
            if channel is None:
                channel = Channel(
                    telegram_chat_id=telegram_chat_id,
                    title=title,
                    username=username,
                    is_default=is_default,
                )
                session.add(channel)
            else:
                channel.title = title
                channel.username = username
                if is_default:
                    channel.is_default = True

            await session.commit()
            await session.refresh(channel)
            return channel


class PostRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_post(
        self,
        user_id: UUID,
        draft: DraftPost,
        status: PostStatus = PostStatus.draft,
        channel_id: UUID | None = None,
    ) -> Post:
        async with self.session_factory() as session:
            post = Post(
                user_id=user_id,
                channel_id=channel_id,
                status=status,
                object_type=draft.object_type,
                source_photo_file_id=draft.photo_file_id,
                caption=draft.caption,
                price_text=draft.price_text,
                availability_text=draft.availability_text,
                story_text=draft.story_text,
                colors=draft.colors,
                style_tags=draft.style_tags,
                published_at=datetime.now(timezone.utc) if status is PostStatus.published else None,
            )
            session.add(post)
            await session.flush()

            session.add(
                PostImage(
                    post_id=post.id,
                    telegram_file_id=draft.photo_file_id,
                    position=0,
                    is_primary=True,
                )
            )

            await session.commit()
            await session.refresh(post)
            return post

    async def list_user_posts(
        self,
        user_id: UUID,
        statuses: Sequence[PostStatus] | None = None,
        limit: int = 5,
    ) -> Sequence[Post]:
        async with self.session_factory() as session:
            query = select(Post).where(Post.user_id == user_id)
            if statuses:
                query = query.where(Post.status.in_(statuses))
            result = await session.execute(
                query.order_by(desc(Post.created_at)).limit(limit)
            )
            return result.scalars().all()

    async def mark_published(
        self,
        post_id: UUID,
        published_message_id: int | None = None,
    ) -> Post | None:
        async with self.session_factory() as session:
            post = await session.get(Post, post_id)
            if post is None:
                return None
            post.status = PostStatus.published
            post.published_at = datetime.now(timezone.utc)
            post.published_message_id = published_message_id
            await session.commit()
            await session.refresh(post)
            return post


class DraftRepository:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        user_repository: UserRepository | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.user_repository = user_repository or UserRepository(session_factory)
        self.post_repository = PostRepository(session_factory)

    async def save_draft(self, user_id: int, draft: DraftPost, status: str = "draft") -> Post:
        user = await self.user_repository.get_or_create(telegram_user_id=user_id)
        return await self.post_repository.create_post(
            user_id=user.id,
            draft=draft,
            status=PostStatus(status),
        )

    async def list_user_drafts(self, user_id: int, limit: int = 5) -> Sequence[Post]:
        user = await self.user_repository.get_by_telegram_user_id(user_id)
        if user is None:
            return []
        return await self.post_repository.list_user_posts(
            user_id=user.id,
            statuses=(PostStatus.draft, PostStatus.ready),
            limit=limit,
        )
