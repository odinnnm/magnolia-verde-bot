"""seed flower dictionary

Revision ID: 20260412_0002
Revises: 20260412_0001
Create Date: 2026-04-12 00:30:00
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "20260412_0002"
down_revision: Union[str, Sequence[str], None] = "20260412_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


flower_dictionary = sa.table(
    "flower_dictionary",
    sa.column("id", sa.String()),
    sa.column("slug", sa.String()),
    sa.column("display_name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("is_active", sa.Boolean()),
)


def upgrade() -> None:
    op.bulk_insert(
        flower_dictionary,
        [
            {"id": str(uuid.uuid4()), "slug": "rose", "display_name": "Роза", "description": "Классический цветок для букетов и композиций.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "peony", "display_name": "Пион", "description": "Объёмный сезонный цветок с мягкой фактурой.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "tulip", "display_name": "Тюльпан", "description": "Лаконичный цветок для весенних букетов.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "lisianthus", "display_name": "Эустома", "description": "Нежный цветок с воздушной формой.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "carnation", "display_name": "Диантус", "description": "Фактурный цветок для современных композиций.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "hydrangea", "display_name": "Гортензия", "description": "Крупный цветок для объёмных букетов.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "ranunculus", "display_name": "Ранункулюс", "description": "Многолепестковый цветок с деликатной формой.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "orchid", "display_name": "Орхидея", "description": "Выразительный акцентный цветок.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "chrysanthemum", "display_name": "Хризантема", "description": "Стойкий цветок для повседневных и праздничных букетов.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "gerbera", "display_name": "Гербера", "description": "Яркий цветок для жизнерадостных композиций.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "alstroemeria", "display_name": "Альстромерия", "description": "Лёгкий цветок для сборных букетов.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "freesia", "display_name": "Фрезия", "description": "Ароматный цветок с тонкой линией бутона.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "anemone", "display_name": "Анемон", "description": "Контрастный акцент для авторских букетов.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "sunflower", "display_name": "Подсолнух", "description": "Яркий сезонный цветок для солнечных композиций.", "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "delphinium", "display_name": "Дельфиниум", "description": "Вертикальный акцент для высоких букетов.", "is_active": True},
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
