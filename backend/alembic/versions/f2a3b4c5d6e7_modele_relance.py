"""modele d'email de relance (rappel de paiement) sur parametres

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-10 17:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('parametres', sa.Column('email_objet_relance', sa.Text(), nullable=True))
    op.add_column('parametres', sa.Column('email_corps_relance', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('parametres', 'email_corps_relance')
    op.drop_column('parametres', 'email_objet_relance')
