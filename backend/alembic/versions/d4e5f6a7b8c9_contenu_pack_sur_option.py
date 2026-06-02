"""contenu_pack editable sur option

Ajoute un conteneur JSON `contenu_pack` sur les options pour permettre l'edition
du descriptif des packs de maintenance (accroche, intro, delai de reponse,
prestations propres au niveau). NULL => fallback sur app.data.packs_maintenance.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-02 11:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'options',
        sa.Column('contenu_pack', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('options', 'contenu_pack')
