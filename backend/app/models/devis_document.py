"""Piece jointe archivee rattachee a un devis (devis signe, contrat, scan...).

Le contenu binaire du fichier est stocke DIRECTEMENT en base (colonne bytea) :
une seule sauvegarde (le dump PostgreSQL) contient ainsi toutes les archives,
sans dossier de fichiers a synchroniser separement. Conforme au besoin
d'archivage des devis et contrats signes retournes par le client.

Soft-delete (corbeille) comme le reste de l'application : une piece n'est jamais
detruite physiquement via l'UI, elle est seulement archivee (archived_at).
"""

from sqlalchemy import String, Integer, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

# Categories metier d'une piece jointe (valeurs sans accents, source de verite ;
# les libelles accentues sont cote frontend, cf. CATEGORIES_DOC dans la page detail).
# Couvre les documents ENVOYES par FluXweb et ceux SIGNES/retournes par le client.
CATEGORIES_DOCUMENT = (
    "devis_envoye",
    "devis_signe",
    "proposition_envoyee",
    "facture_envoyee",
    "contrat_envoye",
    "contrat_signe",
    "avenant_envoye",
    "avenant_signe",
    "bon_commande",
    "annexe",
    "autre",
)
CATEGORIE_DEFAUT = "autre"


class DevisDocument(Base, TimestampMixin, SoftDeleteMixin):
    """Document archive rattache a un devis (PDF/scan signe, contrat, annexe...)."""

    __tablename__ = "devis_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    devis_id: Mapped[int] = mapped_column(
        ForeignKey("devis.id", ondelete="CASCADE"), index=True
    )

    # Categorie metier (cf. CATEGORIES_DOCUMENT).
    categorie: Mapped[str] = mapped_column(
        String(40), default=CATEGORIE_DEFAUT, server_default=CATEGORIE_DEFAUT
    )
    # Etiquette libre (un mot-cle : ex "original", "v1", "ASK VSE").
    tag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Commentaire libre sur la piece.
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Fichier
    nom_fichier: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(
        String(120), default="application/octet-stream"
    )
    taille: Mapped[int] = mapped_column(Integer, default=0)
    contenu: Mapped[bytes] = mapped_column(LargeBinary)

    devis: Mapped["Devis"] = relationship(back_populates="documents")
