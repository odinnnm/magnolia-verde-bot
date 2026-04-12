from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

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

    async def get_by_id(self, post_id: UUID) -> Post | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post)
                .options(selectinload(Post.images))
                .where(Post.id == post_id)
            )
            return result.scalar_one_or_none()

    def build_draft_view(self, post: Post) -> DraftPost:
        photo_file_id = post.source_photo_file_id
        if post.images:
            photo_file_id = post.images[0].telegram_file_id

        return DraftPost(
            photo_file_id=photo_file_id or "",
            object_type=post.object_type or "композиция",
            colors=post.colors or [],
            style_tags=post.style_tags or [],
            caption=post.caption,
            price_text=post.price_text,
            availability_text=post.availability_text,
            story_text=post.story_text,
        )

    async def update_post(
        self,
        post_id: UUID,
        draft: DraftPost,
        status: PostStatus | None = None,
    ) -> Post | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Post)
                .options(selectinload(Post.images))
                .where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()
            if post is None:
                return None

            post.object_type = draft.object_type
            post.source_photo_file_id = draft.photo_file_id
            post.caption = draft.caption
            post.price_text = draft.price_text
            post.availability_text = draft.availability_text
            post.story_text = draft.story_text
            post.colors = draft.colors
            post.style_tags = draft.style_tags
            if status is not None:
                post.status = status

            if post.images:
                primary_image = post.images[0]
                primary_image.telegram_file_id = draft.photo_file_id
                primary_image.is_primary = True
                primary_image.position = 0
            else:
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

    async def set_status(self, post_id: UUID, status: PostStatus) -> Post | None:
        async with self.session_factory() as session:
            post = await session.get(Post, post_id)
            if post is None:
                return None
            post.status = status
            if status is not PostStatus.published:
                post.published_at = None
                post.published_message_id = None
            await session.commit()
            await session.refresh(post)
            return post

    async def mark_failed(self, post_id: UUID, reason: str) -> Post | None:
        async with self.session_factory() as session:
            post = await session.get(Post, post_id)
            if post is None:
                return None
            post.status = PostStatus.failed
            post.failed_reason = reason[:1000]
            await session.commit()
            await session.refresh(post)
            return post

    async def mark_published(
        self,
        post_id: UUID,
        published_message_id: int | None = None,
        channel_id: UUID | None = None,
    ) -> Post | None:
        async with self.session_factory() as session:
            post = await session.get(Post, post_id)
            if post is None:
                return None
            post.status = PostStatus.published
            post.published_at = datetime.now(timezone.utc)
            post.published_message_id = published_message_id
            post.channel_id = channel_id
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
            statuses=(PostStatus.draft, PostStatus.ready, PostStatus.failed),
            limit=limit,
        )

    async def get_user_draft(self, user_id: int, post_id: UUID) -> Post | None:
        user = await self.user_repository.get_by_telegram_user_id(user_id)
        if user is None:
            return None
        post = await self.post_repository.get_by_id(post_id)
        if post is None or post.user_id != user.id:
            return None
        if post.status not in {PostStatus.draft, PostStatus.ready, PostStatus.failed}:
            return None
        return post

    async def archive_user_draft(self, user_id: int, post_id: UUID) -> Post | None:
        post = await self.get_user_draft(user_id, post_id)
        if post is None:
            return None
        return await self.post_repository.set_status(post_id, PostStatus.archived)
