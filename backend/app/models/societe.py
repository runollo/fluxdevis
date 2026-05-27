"""Modele Societe emettrice (BLUELINK INNOVATIONS / FluXweb)."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Societe(Base, TimestampMixin):
    """Societe emettrice des devis et factures.

    Centralise les informations qui etaient dupliquees dans
    build_factures_acompte.py, build_factures_maintenance.py
    et build_template_webflow_comptant.py.
    """

    __tablename__ = "societes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200))
    forme_juridique: Mapped[str] = mapped_column(String(100))
    marque: Mapped[str | None] = mapped_column(String(100))
    adresse: Mapped[str] = mapped_column(String(300))
    cp_ville: Mapped[str] = mapped_column(String(100))
    siret: Mapped[str] = mapped_column(String(20))
    rcs: Mapped[str | None] = mapped_column(String(100))
    tva_intracom: Mapped[str | None] = mapped_column(String(20))
    telephone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))
    site_web: Mapped[str | None] = mapped_column(String(200))
    iban: Mapped[str | None] = mapped_column(String(40))
    bic: Mapped[str | None] = mapped_column(String(15))
    logo_path: Mapped[str | None] = mapped_column(Text)
