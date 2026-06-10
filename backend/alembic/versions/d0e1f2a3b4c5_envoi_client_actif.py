"""garde-fou envoi direct au client (parametres.envoi_client_actif)

Interrupteur de securite : autorise ou non l'envoi DIRECT au client. Desactive
par defaut (false) ; l'envoi "a moi" reste toujours possible.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-10 15:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'parametres',
        sa.Column('envoi_client_actif', sa.Boolean(), server_default='false', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('parametres', 'envoi_client_actif')
