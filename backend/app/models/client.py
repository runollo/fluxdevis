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
    raison_sociale: Mapped[str] = mapped_column(String(200), index=True)
    adresse: Mapped[str | None] = mapped_column(String(300))
    code_postal: Mapped[str | None] = mapped_column(String(10))
    ville: Mapped[str | None] = mapped_column(String(100))
    interlocuteur: Mapped[str | None] = mapped_column(String(200))
    telephone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(200))
    siret: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    actif: Mapped[bool] = mapped_column(default=True)

    # Relations
    devis: Mapped[list["Devis"]] = relationship(back_populates="client")
