"""pieces jointes archivees sur devis + document officiel externe

Cree la table `devis_documents` (pieces jointes stockees en base : devis signe,
contrat signe, scans...) et ajoute sur `devis` les champs `reference_externe` et
`date_signature` pour tracer le cas ou le document officiel qui fait foi est une
piece jointe externe (devis repris de l'ancien systeme, retourne signe).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-10 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'devis_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('devis_id', sa.Integer(), nullable=False),
        sa.Column('categorie', sa.String(length=40), server_default='autre', nullable=False),
        sa.Column('tag', sa.String(length=80), nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('nom_fichier', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=120), nullable=False),
        sa.Column('taille', sa.Integer(), nullable=False),
        sa.Column('contenu', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['devis_id'], ['devis.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_devis_documents_devis_id'), 'devis_documents', ['devis_id'])

    op.add_column('devis', sa.Column('reference_externe', sa.String(length=60), nullable=True))
    op.add_column('devis', sa.Column('date_signature', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('devis', 'date_signature')
    op.drop_column('devis', 'reference_externe')
    op.drop_index(op.f('ix_devis_documents_devis_id'), table_name='devis_documents')
    op.drop_table('devis_documents')
