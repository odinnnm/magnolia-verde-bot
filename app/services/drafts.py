from app.schemas.draft import DraftPost, PhotoAnalysis
from app.services.caption import CaptionService


class DraftFactoryService:
    def __init__(self, caption_service: CaptionService) -> None:
        self.caption_service = caption_service

    def create_from_analysis(self, photo_file_id: str, analysis: PhotoAnalysis) -> DraftPost:
        return DraftPost(
            photo_file_id=photo_file_id,
            object_type=analysis.object_type,
            flowers=analysis.flower_names,
            colors=analysis.colors,
            style_tags=analysis.style_tags,
            caption=self.caption_service.generate_caption(analysis),
        )

    def normalize_price(self, raw_price: str) -> str:
        normalized = "".join(symbol for symbol in raw_price if symbol.isdigit())
        if not normalized:
            return raw_price.strip()
        return f"Стоимость: {normalized} ₽"

    def normalize_availability(self, raw_value: str) -> str:
        value = raw_value.strip()
        if not value:
            return "Наличие уточняется"
        normalized = value.lower()
        if normalized in {"в наличии", "есть"}:
            return "В наличии"
        if normalized in {"под заказ", "заказ"}:
            return "Под заказ"
        if normalized in {"ограничено", "ограниченное количество"}:
            return "Ограниченное количество"
        return value[:120]
