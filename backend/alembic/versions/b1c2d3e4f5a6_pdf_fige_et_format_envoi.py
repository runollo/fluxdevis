"""figement du PDF a l'emission + format d'envoi (tracabilite)

Revision ID: b1c2d3e4f5a6
Revises: 29141829c688
Create Date: 2026-06-12 18:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '29141829c688'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PDF fige a l'emission (exemplaire legal conserve tel quel).
    op.add_column('factures', sa.Column('pdf_fige', sa.LargeBinary(), nullable=True))
    op.add_column('factures', sa.Column('pdf_fige_le', sa.DateTime(timezone=True), nullable=True))
    # Format de la piece jointe pour chaque envoi (tracabilite).
    op.add_column('facture_envois', sa.Column('format', sa.String(length=8), server_default='pdf', nullable=False))


def downgrade() -> None:
    op.drop_column('facture_envois', 'format')
    op.drop_column('factures', 'pdf_fige_le')
    op.drop_column('factures', 'pdf_fige')
