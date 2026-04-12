from dataclasses import dataclass

from app.db.repositories import DraftRepository
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


def build_service_container(db: DatabaseManager) -> ServiceContainer:
    caption = CaptionService()
    return ServiceContainer(
        photo_analyzer=PhotoAnalyzerService(),
        caption=caption,
        draft_factory=DraftFactoryService(caption_service=caption),
        publisher=PublisherService(),
        draft_repository=DraftRepository(db.session_factory),
    )
