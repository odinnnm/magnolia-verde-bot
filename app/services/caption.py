from app.schemas.draft import PhotoAnalysis


class CaptionService:
    def generate_caption(self, analysis: PhotoAnalysis, premium: bool = False) -> str:
        flowers = ", ".join(analysis.flower_names)
        colors = ", ".join(analysis.colors)
        base = (
            f"Нежная авторская композиция в палитре {colors}. "
            f"В букете просматриваются {flowers}. "
            "Подойдёт для комплимента, дня рождения или красивого знака внимания."
        )
        if premium:
            return (
                base
                + " Более выразительная фактура и собранное настроение делают композицию особенно эффектной."
            )
        return base

    def shorten_caption(self, text: str) -> str:
        parts = [part.strip() for part in text.split(". ") if part.strip()]
        return ". ".join(parts[:2]).strip()

    def build_story(self, analysis: PhotoAnalysis) -> str | None:
        if not analysis.primary_flower or (analysis.primary_flower.confidence or 0) < 0.7:
            return None
        return (
            f"{analysis.primary_flower.name.capitalize()} ценится за выразительную форму "
            "и мягкую, почти воздушную фактуру лепестков."
        )
