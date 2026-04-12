"""seed flower dictionary

Revision ID: 20260412_0002
Revises: 20260412_0001
Create Date: 2026-04-12 00:30:00
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy.dialects import postgresql


revision: str = "20260412_0002"
down_revision: Union[str, Sequence[str], None] = "20260412_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


flower_dictionary = sa.table(
    "flower_dictionary",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("slug", sa.String()),
    sa.column("display_name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("is_active", sa.Boolean()),
)


def upgrade() -> None:
    op.bulk_insert(
        flower_dictionary,
        [
            {
                "id": uuid.uuid4(),
                "slug": "rose",
                "display_name": "Роза",
                "description": "Классика букетов. Ассоциация: романтика, внимание, тёплый жест.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "peony",
                "display_name": "Пион",
                "description": "Пышный сезонный цветок. Ассоциация: нежность, лето, изобилие.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "tulip",
                "display_name": "Тюльпан",
                "description": "Лаконичный весенний цветок. Ассоциация: свежесть, лёгкость, начало сезона.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "lisianthus",
                "display_name": "Эустома",
                "description": "Воздушный цветок с мягкой формой. Ассоциация: деликатность и спокойствие.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "carnation",
                "display_name": "Диантус",
                "description": "Фактурный акцент для современных букетов. Ассоциация: ритм и графика.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "hydrangea",
                "display_name": "Гортензия",
                "description": "Крупный объёмный цветок. Ассоциация: щедрость, облако, мягкий силуэт.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "ranunculus",
                "display_name": "Ранункулюс",
                "description": "Многолепестковый цветок. Ассоциация: утончённость и камерная роскошь.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "orchid",
                "display_name": "Орхидея",
                "description": "Выразительный акцентный цветок. Ассоциация: экзотика, статус, изящество.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "chrysanthemum",
                "display_name": "Хризантема",
                "description": "Стойкий цветок на каждый день. Ассоциация: надёжность и уют.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "gerbera",
                "display_name": "Гербера",
                "description": "Яркий цветок с открытой формой. Ассоциация: радость, энергия, улыбка.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "alstroemeria",
                "display_name": "Альстромерия",
                "description": "Лёгкий цветок для сборных букетов. Ассоциация: движение и лёгкость.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "freesia",
                "display_name": "Фрезия",
                "description": "Ароматный цветок с тонкой линией бутона. Ассоциация: чистота и свежесть.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "anemone",
                "display_name": "Анемон",
                "description": "Контрастный акцент. Ассоциация: глубина, характер, художественный штрих.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "sunflower",
                "display_name": "Подсолнух",
                "description": "Яркий сезонный цветок. Ассоциация: солнце, тепло, щедрое настроение.",
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "delphinium",
                "display_name": "Дельфиниум",
                "description": "Вертикальный акцент для высоких букетов. Ассоциация: воздух и высота.",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM flower_dictionary
        WHERE slug IN (
            'rose', 'peony', 'tulip', 'lisianthus', 'carnation',
            'hydrangea', 'ranunculus', 'orchid', 'chrysanthemum', 'gerbera',
            'alstroemeria', 'freesia', 'anemone', 'sunflower', 'delphinium'
        )
        """
    )
