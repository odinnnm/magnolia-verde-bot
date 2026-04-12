from aiogram.types import Message

from app.schemas.draft import FlowerCandidate, PhotoAnalysis


class PhotoAnalyzerService:
    async def analyze_photo(self, message: Message) -> PhotoAnalysis:
        return PhotoAnalysis(
            object_type="букет",
            flowers=[
                FlowerCandidate(name="роза", confidence=0.83),
                FlowerCandidate(name="эустома", confidence=0.71),
                FlowerCandidate(name="диантус", confidence=0.64),
            ],
            colors=["белый", "розовый"],
            style_tags=["нежный", "воздушный"],
            confidence_overall=0.76,
        )
