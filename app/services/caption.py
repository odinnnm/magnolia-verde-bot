from app.schemas.draft import PhotoAnalysis


class CaptionService:
    def _build_caption_variants(self, analysis: PhotoAnalysis, premium: bool = False) -> list[str]:
        flowers = ", ".join(analysis.flower_names) or "сезонные цветы"
        colors = ", ".join(analysis.colors) or "мягкой палитре"

        variants = [
            (
                f"Нежная авторская композиция в палитре {colors}. "
                f"В букете просматриваются {flowers}. "
                "Подойдёт для комплимента, дня рождения или красивого знака внимания."
            ),
            (
                f"Воздушная композиция в оттенках {colors}. "
                f"В составе читаются {flowers}. "
                "Такой букет легко подарить для тёплого жеста, праздника или просто без повода."
            ),
            (
                f"Авторский букет в гамме {colors} с акцентом на {flowers}. "
                "Собран для тех случаев, когда хочется подарить деликатное и выразительное настроение."
            ),
            (
                f"Лёгкая цветочная композиция в палитре {colors}, где особенно заметны {flowers}. "
                "Подойдёт для поздравления, благодарности или красивого комплимента."
            ),
        ]

        if premium:
            variants.extend(
                [
                    (
                        f"Премиальная композиция в оттенках {colors} с выразительной фактурой {flowers}. "
                        "Собранный силуэт и благородное настроение делают её особенно эффектной."
                    ),
                    (
                        f"Элегантный авторский букет в гамме {colors}, где раскрываются {flowers}. "
                        "Более собранный характер и выразительная пластика делают композицию по-настоящему премиальной."
                    ),
                ]
            )

        return variants

    def generate_caption(self, analysis: PhotoAnalysis, premium: bool = False) -> str:
        return self._build_caption_variants(analysis, premium=premium)[0]

    def regenerate_caption(self, analysis: PhotoAnalysis, current_caption: str | None = None) -> str | None:
        if not analysis.flower_names and not analysis.colors:
            return None
        variants = self._build_caption_variants(analysis, premium=False)
        if current_caption:
            for variant in variants:
                if variant != current_caption:
                    return variant
        return variants[0] if variants else None

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
