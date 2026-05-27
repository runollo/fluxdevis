"""Modele Offre (catalogue des offres web)."""

from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Offre(Base, TimestampMixin):
    """Offre commerciale (Presence, Croissance, Serenite, Premium, Shopify...).

    Correspond aux 10 offres de donnees_catalogue.xlsx feuille "Offres".
    """

    __tablename__ = "offres"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), unique=True)
    type_site: Mapped[str] = mapped_column(String(100))  # "Webflow" / "Shopify"
    type_offre: Mapped[str] = mapped_column(String(100))  # "Site vitrine essentiel", etc.
    tarif_achat: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    taux_marge: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tarif_vente_conseille: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    pages: Mapped[int] = mapped_column(Integer)
    heures: Mapped[int] = mapped_column(Integer)
    commission_apporteur: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    inclusions: Mapped[list["OptionInclusion"]] = relationship(back_populates="offre")
