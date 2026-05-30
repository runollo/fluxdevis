"""Modeles Option et OptionInclusion."""

from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Option(Base, TimestampMixin):
    """Option ou pack de maintenance.

    Correspond aux 52 options de donnees_catalogue.xlsx feuille "Options" (27 champs).

    Les champs calcules (setup_achat, mensuel_achat, vente_setup, vente_mensuel)
    sont stockes en BDD et recalcules via un @hybrid_property ou au moment du save.
    """

    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(200))
    categorie: Mapped[str] = mapped_column(String(50))
    # OPTION_SETUP, OPTION_RECURRENT, PACK
    type_ligne: Mapped[str] = mapped_column(String(20))

    # Donnees source (editables)
    heures_setup: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    heures_mensuel: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    prix_heure: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=27)
    taux_marge: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.30"))

    # Prix calcules (= source × formules)
    setup_achat: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    mensuel_achat: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    vente_setup: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    vente_mensuel: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Hebergement
    prix_hebergement: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Configuration
    commentaire: Mapped[str | None] = mapped_column(Text)
    selection_regle: Mapped[str] = mapped_column(String(20), default="OPTIONNEL")
    quantite_defaut: Mapped[int] = mapped_column(Integer, default=0)
    unite: Mapped[str] = mapped_column(String(20), default="unite")

    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    # Relations
    inclusions: Mapped[list["OptionInclusion"]] = relationship(back_populates="option")

    def recalculer_prix(self):
        """Recalcule les 4 prix derives, a l'identique des formules du catalogue
        Excel (donnees_catalogue.xlsx, feuille Options).

        Formules Excel :
          setup_achat   = prix_heure * heures_setup                         (X*V)
          mensuel_achat = prix_heure * heures_mensuel + prix_hebergement    (X*W+U)
          vente_setup   = setup_achat   * (1 + taux_marge)                  (E*(1+G))
          vente_mensuel = mensuel_achat * (1 + taux_marge)                  (F*(1+G))

        Le terme + prix_hebergement sur le cout mensuel est essentiel pour les
        packs de maintenance Webflow (hebergement 31 EUR/mois inclus) ; il etait
        omis auparavant, ce qui sous-evaluait fortement la maintenance.
        """
        self.setup_achat = self.prix_heure * self.heures_setup
        self.mensuel_achat = self.prix_heure * self.heures_mensuel + self.prix_hebergement
        self.vente_setup = self.setup_achat * (1 + self.taux_marge)
        self.vente_mensuel = self.mensuel_achat * (1 + self.taux_marge)


class OptionInclusion(Base):
    """Table de liaison : quelle option est incluse dans quelle offre.

    Remplace les 10 colonnes incl_presence ... incl_sh_upgrade
    par une vraie relation M:N normalisee.
    """

    __tablename__ = "option_inclusions"
    __table_args__ = (
        UniqueConstraint("option_id", "offre_id", name="uq_option_offre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("options.id", ondelete="CASCADE"))
    offre_id: Mapped[int] = mapped_column(ForeignKey("offres.id", ondelete="CASCADE"))

    # Relations
    option: Mapped["Option"] = relationship(back_populates="inclusions")
    offre: Mapped["Offre"] = relationship(back_populates="inclusions")
