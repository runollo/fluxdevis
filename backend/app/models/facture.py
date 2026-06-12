"""Modeles Facture, FactureLigne, Echeance."""

from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Date, DateTime, ForeignKey, Text, LargeBinary, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class TypeFacture(str, enum.Enum):
    ACOMPTE = "acompte"
    MAINTENANCE = "maintenance"
    SOLDE = "solde"
    AVOIR = "avoir"  # Facture d'avoir (annulation/rectification) en montants negatifs


class StatutFacture(str, enum.Enum):
    BROUILLON = "brouillon"
    EMISE = "emise"
    PAYEE = "payee"
    EN_RETARD = "en_retard"
    ANNULEE = "annulee"


class Facture(Base, TimestampMixin, SoftDeleteMixin):
    """Facture (acompte ou maintenance).

    Regroupe les donnees de build_factures_acompte.py
    et build_factures_maintenance.py.
    """

    __tablename__ = "factures"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    type: Mapped[TypeFacture] = mapped_column(SAEnum(TypeFacture))
    statut: Mapped[StatutFacture] = mapped_column(
        SAEnum(StatutFacture), default=StatutFacture.BROUILLON
    )

    # Lien au devis
    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id"))

    # Pour un avoir (type AVOIR) : la facture d'origine qu'il annule/rectifie.
    facture_origine_id: Mapped[int | None] = mapped_column(
        ForeignKey("factures.id"), nullable=True
    )

    # Dates
    date_emission: Mapped[date] = mapped_column(Date)
    date_echeance: Mapped[date] = mapped_column(Date)

    # Periode (pour les factures de maintenance)
    periode_debut: Mapped[date | None] = mapped_column(Date)
    periode_fin: Mapped[date | None] = mapped_column(Date)

    # Objet
    objet: Mapped[str] = mapped_column(Text)

    # Montants
    total_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Paiement
    date_paiement: Mapped[date | None] = mapped_column(Date)
    moyen_paiement: Mapped[str | None] = mapped_column(String(50))

    # Document fige a l'emission : exemplaire legal du PDF, conserve tel quel.
    # NULL tant que la facture est en brouillon (ou si la conversion PDF a echoue
    # a l'emission -> regenerable). Une fois present, il est resservi a chaque
    # telechargement/envoi (le document ne change plus, meme si la societe est editee).
    pdf_fige: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    pdf_fige_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    devis: Mapped["Devis"] = relationship(back_populates="factures")
    lignes: Mapped[list["FactureLigne"]] = relationship(
        back_populates="facture", cascade="all, delete-orphan"
    )
    echeances: Mapped[list["Echeance"]] = relationship(
        back_populates="facture", cascade="all, delete-orphan"
    )
    envois: Mapped[list["FactureEnvoi"]] = relationship(
        back_populates="facture", cascade="all, delete-orphan",
        order_by="FactureEnvoi.date_envoi",
    )


class FactureEnvoi(Base):
    """Trace d'un envoi de facture par email (historique + alerte au renvoi)."""

    __tablename__ = "facture_envois"

    id: Mapped[int] = mapped_column(primary_key=True)
    facture_id: Mapped[int] = mapped_column(
        ForeignKey("factures.id", ondelete="CASCADE"), index=True
    )
    date_envoi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    # "client" (envoi direct) ou "expediteur" (a soi-meme, pour transferer).
    mode: Mapped[str] = mapped_column(String(20))
    destinataire: Mapped[str] = mapped_column(String(200))
    # Format de la piece jointe envoyee ("pdf" en pratique).
    format: Mapped[str] = mapped_column(String(8), default="pdf", server_default="pdf")

    facture: Mapped["Facture"] = relationship(back_populates="envois")


class CompteurFacture(Base):
    """Compteur de numerotation des factures, un par annee.

    `dernier` est le dernier numero attribue pour l'annee. Il ne fait
    qu'augmenter (jamais de reutilisation) : le numero legal F<annee>-NNN est
    attribue a l'EMISSION via une increment atomique. Garantit une sequence
    chronologique continue sans trou, independante des brouillons supprimes.
    """

    __tablename__ = "compteur_facture"

    annee: Mapped[int] = mapped_column(Integer, primary_key=True)
    dernier: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class CompteurAvoir(Base):
    """Compteur de numerotation des avoirs, un par annee.

    Sequence DISTINCTE des factures (numero AV<annee>-NNN), continue et sans
    trou, attribuee a l'emission de l'avoir.
    """

    __tablename__ = "compteur_avoir"

    annee: Mapped[int] = mapped_column(Integer, primary_key=True)
    dernier: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class FactureLigne(Base):
    """Ligne de detail d'une facture."""

    __tablename__ = "facture_lignes"

    id: Mapped[int] = mapped_column(primary_key=True)
    facture_id: Mapped[int] = mapped_column(ForeignKey("factures.id", ondelete="CASCADE"))
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    designation: Mapped[str] = mapped_column(String(500))
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    taux_tva: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.20"))
    montant_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    facture: Mapped["Facture"] = relationship(back_populates="lignes")


class Echeance(Base):
    """Echeance de paiement d'une facture.

    Correspond a la structure ECHEANCES de build_factures_acompte.py.
    """

    __tablename__ = "echeances"

    id: Mapped[int] = mapped_column(primary_key=True)
    facture_id: Mapped[int] = mapped_column(ForeignKey("factures.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(200))
    date_echeance: Mapped[date] = mapped_column(Date)
    montant_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    montant_ttc: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payee: Mapped[bool] = mapped_column(default=False)

    facture: Mapped["Facture"] = relationship(back_populates="echeances")
