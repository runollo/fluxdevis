"""parametres applicatifs (singleton) : reglages SMTP editables depuis l'UI

Table `parametres` (une ligne, id=1) pour les reglages modifiables depuis la page
Parametres : envoi d'emails (SMTP) aujourd'hui, extensible ensuite. NULL = repli .env.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-10 13:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'parametres',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('smtp_host', sa.String(length=200), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('smtp_starttls', sa.Boolean(), nullable=True),
        sa.Column('smtp_user', sa.String(length=200), nullable=True),
        sa.Column('smtp_password', sa.String(length=255), nullable=True),
        sa.Column('smtp_from', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('parametres')
