"""Modeles Facture, FactureLigne, Echeance."""

from datetime import date
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Date, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class TypeFacture(str, enum.Enum):
    ACOMPTE = "acompte"
    MAINTENANCE = "maintenance"
    SOLDE = "solde"


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

    # Relations
    devis: Mapped["Devis"] = relationship(back_populates="factures")
    lignes: Mapped[list["FactureLigne"]] = relationship(
        back_populates="facture", cascade="all, delete-orphan"
    )
    echeances: Mapped[list["Echeance"]] = relationship(
        back_populates="facture", cascade="all, delete-orphan"
    )


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
