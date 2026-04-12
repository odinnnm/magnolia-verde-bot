from dataclasses import dataclass

from app.db.repositories import ChannelRepository, DraftRepository, PostRepository, UserRepository
from app.db.session import DatabaseManager
from app.services.analyzer import PhotoAnalyzerService
from app.services.caption import CaptionService
from app.services.drafts import DraftFactoryService
from app.services.publisher import PublisherService


@dataclass(slots=True)
class ServiceContainer:
    photo_analyzer: PhotoAnalyzerService
    caption: CaptionService
    draft_factory: DraftFactoryService
    publisher: PublisherService
    draft_repository: DraftRepository
    user_repository: UserRepository
    channel_repository: ChannelRepository
    post_repository: PostRepository


def build_service_container(db: DatabaseManager) -> ServiceContainer:
    caption = CaptionService()
    user_repository = UserRepository(db.session_factory)
    channel_repository = ChannelRepository(db.session_factory)
    post_repository = PostRepository(db.session_factory)
    return ServiceContainer(
        photo_analyzer=PhotoAnalyzerService(),
        caption=caption,
        draft_factory=DraftFactoryService(caption_service=caption),
        publisher=PublisherService(),
        draft_repository=DraftRepository(db.session_factory, user_repository=user_repository),
        user_repository=user_repository,
        channel_repository=channel_repository,
        post_repository=post_repository,
    )
