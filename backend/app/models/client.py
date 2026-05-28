"""Modele Client."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    """Client (prospect ou actif).

    Correspond aux donnees de contact.xlsx / Contacts_DB.
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identification societe
    raison_sociale: Mapped[str] = mapped_column(String(200), index=True)
    forme_juridique: Mapped[str | None] = mapped_column(String(50))
    siret: Mapped[str | None] = mapped_column(String(20))
    code_ape: Mapped[str | None] = mapped_column(String(10))
    rcs: Mapped[str | None] = mapped_column(String(100))
    tva_intracom: Mapped[str | None] = mapped_column(String(20))

    # Adresse
    adresse: Mapped[str | None] = mapped_column(String(300))
    complement_adresse: Mapped[str | None] = mapped_column(String(300))
    code_postal: Mapped[str | None] = mapped_column(String(10))
    ville: Mapped[str | None] = mapped_column(String(100))
    pays: Mapped[str | None] = mapped_column(String(50), default="France")

    # Contact principal
    civilite: Mapped[str | None] = mapped_column(String(10))
    interlocuteur: Mapped[str | None] = mapped_column(String(200))
    fonction: Mapped[str | None] = mapped_column(String(100))
    telephone: Mapped[str | None] = mapped_column(String(30))
    mobile: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(200))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    actif: Mapped[bool] = mapped_column(default=True)

    # Relations
    devis: Mapped[list["Devis"]] = relationship(back_populates="client")
