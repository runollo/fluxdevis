"""Modeles Devis, DevisLigne, DevisOptionLigne."""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Integer, Boolean, Date, ForeignKey, Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin


class ModeReglement(str, enum.Enum):
    COMPTANT = "Comptant"
    LEASING = "Leasing"


class PlanPaiement(str, enum.Enum):
    CENT = "100%"
    CINQUANTE_CINQUANTE = "50/50"
    CINQUANTE_VINGTCINQ_VINGTCINQ = "50/25/25"
    VINGTCINQ_X4 = "25/25/25/25"


class StatutDevis(str, enum.Enum):
    BROUILLON = "brouillon"
    ENVOYE = "envoye"
    ACCEPTE = "accepte"
    REFUSE = "refuse"
    EXPIRE = "expire"


class Devis(Base, TimestampMixin):
    """Devis client — snapshot fige des prix au moment de l'emission.

    Regroupe les donnees de Simu_live + Devis_client + Devis_params.
    """

    __tablename__ = "devis"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    # Statut
    statut: Mapped[StatutDevis] = mapped_column(
        SAEnum(StatutDevis), default=StatutDevis.BROUILLON
    )

    # Dates
    date_emission: Mapped[date] = mapped_column(Date)
    date_validite: Mapped[date] = mapped_column(Date)
    # Mise en ligne du site : declenche la facturation du recurrent (maintenance).
    # Independante du plan de paiement du setup.
    date_mise_en_ligne: Mapped[date | None] = mapped_column(Date)

    # Client (FK + snapshot des infos au moment du devis)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client_raison_sociale: Mapped[str] = mapped_column(String(200))
    client_adresse: Mapped[str | None] = mapped_column(String(300))
    client_cp: Mapped[str | None] = mapped_column(String(10))
    client_ville: Mapped[str | None] = mapped_column(String(100))
    client_interlocuteur: Mapped[str | None] = mapped_column(String(200))
    client_telephone: Mapped[str | None] = mapped_column(String(30))
    client_siret: Mapped[str | None] = mapped_column(String(20))

    # Offre (FK + snapshot)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offres.id"))
    offre_nom: Mapped[str] = mapped_column(String(200))
    offre_type_site: Mapped[str] = mapped_column(String(100))
    offre_prix_catalogue: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Mode et paiement
    mode_reglement: Mapped[ModeReglement] = mapped_column(SAEnum(ModeReglement))
    plan_paiement: Mapped[PlanPaiement | None] = mapped_column(SAEnum(PlanPaiement))

    # Prix affiches (figes)
    prix_vente_final: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_prestations_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_options_setup_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_pack_maintenance_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_options_recurrent_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Remises
    remise_pct_setup: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    remise_pct_recurrent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    remise_eur_setup: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    remise_eur_recurrent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Marge
    marge_additionnelle: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Leasing specifique
    duree_financement_mois: Mapped[int | None] = mapped_column(Integer)
    coefficient_locam: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    pct_maintenance_locam: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    garantie_web: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    montant_finance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    loyer_mensuel: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Totaux calcules
    total_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_tva: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Textes personnalises (ex Devis_params)
    commercial: Mapped[str | None] = mapped_column(String(200))
    accroche: Mapped[str | None] = mapped_column(Text)
    note_commerciale: Mapped[str | None] = mapped_column(Text)

    # Relations
    client: Mapped["Client"] = relationship(back_populates="devis")
    lignes: Mapped[list["DevisLigne"]] = relationship(
        back_populates="devis", cascade="all, delete-orphan"
    )
    options: Mapped[list["DevisOptionLigne"]] = relationship(
        back_populates="devis", cascade="all, delete-orphan"
    )
    articles_offerts: Mapped[list["DevisArticleOffert"]] = relationship(
        back_populates="devis", cascade="all, delete-orphan"
    )
    factures: Mapped[list["Facture"]] = relationship(back_populates="devis")


class DevisLigne(Base):
    """Ligne de prestation sur mesure dans un devis (3 max dans l'Excel actuel)."""

    __tablename__ = "devis_lignes"

    id: Mapped[int] = mapped_column(primary_key=True)
    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id", ondelete="CASCADE"))
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    designation: Mapped[str] = mapped_column(String(300))
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire_achat: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    prix_unitaire_vente: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    devis: Mapped["Devis"] = relationship(back_populates="lignes")


class DevisOptionLigne(Base):
    """Option selectionnee dans un devis — avec prix fige."""

    __tablename__ = "devis_option_lignes"

    id: Mapped[int] = mapped_column(primary_key=True)
    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id", ondelete="CASCADE"))
    option_id: Mapped[int] = mapped_column(ForeignKey("options.id"))
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    # Snapshot fige au moment du devis
    code: Mapped[str] = mapped_column(String(50))
    nom: Mapped[str] = mapped_column(String(200))
    type_ligne: Mapped[str] = mapped_column(String(20))
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_setup_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    prix_mensuel_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    inclus: Mapped[bool] = mapped_column(Boolean, default=False)

    devis: Mapped["Devis"] = relationship(back_populates="options")


class DevisArticleOffert(Base):
    """Article offert dans un devis (5 max dans l'Excel actuel)."""

    __tablename__ = "devis_articles_offerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    devis_id: Mapped[int] = mapped_column(ForeignKey("devis.id", ondelete="CASCADE"))
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    designation: Mapped[str] = mapped_column(String(300))
    prix_achat: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    prix_vente: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    devis: Mapped["Devis"] = relationship(back_populates="articles_offerts")
