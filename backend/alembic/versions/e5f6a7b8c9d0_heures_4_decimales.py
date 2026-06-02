"""heures en 4 decimales sur option

Passe Option.heures_setup et heures_mensuel de Numeric(8,2) a Numeric(8,4) pour
permettre d'atteindre un prix de vente mensuel cible precis en n'ajustant que les
heures (prix/heure et marge figes). Aucune perte : les valeurs existantes a 2
decimales restent valides.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-02 12:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('options', 'heures_setup',
                    type_=sa.Numeric(8, 4), existing_nullable=False)
    op.alter_column('options', 'heures_mensuel',
                    type_=sa.Numeric(8, 4), existing_nullable=False)


def downgrade() -> None:
    op.alter_column('options', 'heures_mensuel',
                    type_=sa.Numeric(8, 2), existing_nullable=False)
    op.alter_column('options', 'heures_setup',
                    type_=sa.Numeric(8, 2), existing_nullable=False)
