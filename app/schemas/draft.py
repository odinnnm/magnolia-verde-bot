from pydantic import BaseModel, Field


class FlowerCandidate(BaseModel):
    name: str
    confidence: float | None = None


class PhotoAnalysis(BaseModel):
    object_type: str
    flowers: list[FlowerCandidate] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    confidence_overall: float | None = None

    @property
    def flower_names(self) -> list[str]:
        return [flower.name for flower in self.flowers]

    @property
    def primary_flower(self) -> FlowerCandidate | None:
        return self.flowers[0] if self.flowers else None


class DraftPost(BaseModel):
    photo_file_id: str
    object_type: str
    flowers: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    caption: str
    price_text: str | None = None
    availability_text: str | None = None
    story_text: str | None = None

    def to_analysis(self) -> PhotoAnalysis:
        return PhotoAnalysis(
            object_type=self.object_type,
            flowers=[FlowerCandidate(name=name) for name in self.flowers],
            colors=self.colors,
            style_tags=self.style_tags,
        )

    def build_preview_text(self) -> str:
        preview = (
            "Распознано:\n"
            f"• Тип: {self.object_type}\n"
            f"• Цветы: {', '.join(self.flowers)}\n"
            f"• Палитра: {', '.join(self.colors)}\n"
            f"• Стиль: {', '.join(self.style_tags)}\n\n"
            f"Предпросмотр подписи:\n{self.caption}"
        )
        if self.price_text:
            preview += f"\n\n{self.price_text}"
        if self.availability_text:
            preview += f"\n{self.availability_text}"
        if self.story_text:
            preview += f"\n\nИстория:\n{self.story_text}"
        return preview

    def build_publish_caption(self) -> str:
        parts = [self.caption]
        if self.price_text:
            parts.append(self.price_text)
        if self.availability_text:
            parts.append(self.availability_text)
        if self.story_text:
            parts.append(self.story_text)
        parts.append("Магнолия Верде")
        return "\n\n".join(parts)
