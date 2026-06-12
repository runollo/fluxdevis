"""Modeles Devis, DevisLigne, DevisOptionLigne."""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Integer, Boolean, Date, ForeignKey, Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

# Type de document : un devis (contractuel, signature/IBAN/echeancier) ou une
# proposition budgetaire (estimation commerciale non contractuelle, document court).
DOC_DEVIS = "devis"
DOC_PROPOSITION = "proposition_budgetaire"


class ModeReglement(str, enum.Enum):
    COMPTANT = "Comptant"
    LEASING = "Leasing"


class PlanPaiement(str, enum.Enum):
    CENT = "100%"
    CINQUANTE_CINQUANTE = "50/50"
    TIERS = "33/33/33"
    CINQUANTE_VINGTCINQ_VINGTCINQ = "50/25/25"
    VINGTCINQ_X4 = "25/25/25/25"


class StatutDevis(str, enum.Enum):
    BROUILLON = "brouillon"
    ENVOYE = "envoye"
    ACCEPTE = "accepte"
    REFUSE = "refuse"
    EXPIRE = "expire"


class Devis(Base, TimestampMixin, SoftDeleteMixin):
    """Devis client — snapshot fige des prix au moment de l'emission.

    Regroupe les donnees de Simu_live + Devis_client + Devis_params.
    """

    __tablename__ = "devis"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    # Type de document : "devis" (defaut, contractuel) ou "proposition_budgetaire".
    # Pilote le titre, le prefixe de reference (D- / PB-) et l'affichage des
    # elements contractuels (signature, IBAN, "Bon pour accord", echeancier).
    document_type: Mapped[str] = mapped_column(
        String(30), default=DOC_DEVIS, server_default=DOC_DEVIS
    )

    # Versioning : un meme devis peut etre revise plusieurs fois (negociation).
    # - racine_id : id du tout premier devis de la lignee (None pour la racine elle-meme).
    # - version : 1, 2, 3... (la reference porte le suffixe -V2, -V3 a partir de la V2).
    # - version_active : seule la derniere version est active ; les precedentes restent
    #   consultables en lecture seule mais masquees des listes par defaut.
    racine_id: Mapped[int | None] = mapped_column(ForeignKey("devis.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    version_active: Mapped[bool] = mapped_column(Boolean, default=True)

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

    # Document officiel externe : quand le vrai devis qui fait foi n'est pas celui
    # genere par l'application mais une piece jointe signee (ex devis repris de
    # l'ancien systeme, retourne signe par le client). Le devis applicatif devient
    # alors une RECONSTITUTION informative ; ces deux champs tracent l'original.
    # - reference_externe : numero/identifiant d'origine du document signe.
    # - date_signature : date a laquelle le client a retourne le document signe.
    reference_externe: Mapped[str | None] = mapped_column(String(60), nullable=True)
    date_signature: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Echeancier de l'acompte : date de depart (def = date_emission) et pas en
    # jours entre versements. Servent a pre-remplir les dates d'echeance des
    # factures d'acompte (dates restent editables ligne par ligne ensuite).
    date_debut_echeancier: Mapped[date | None] = mapped_column(Date)
    intervalle_echeance_jours: Mapped[int] = mapped_column(Integer, default=30, server_default="30")

    # Client (FK + snapshot des infos au moment du devis)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client_raison_sociale: Mapped[str] = mapped_column(String(200))
    client_adresse: Mapped[str | None] = mapped_column(String(300))
    client_cp: Mapped[str | None] = mapped_column(String(10))
    client_ville: Mapped[str | None] = mapped_column(String(100))
    client_interlocuteur: Mapped[str | None] = mapped_column(String(200))
    client_telephone: Mapped[str | None] = mapped_column(String(30))
    client_email: Mapped[str | None] = mapped_column(String(200))
    client_siret: Mapped[str | None] = mapped_column(String(20))
    # N° TVA intracom du client (mention obligatoire si client pro redevable,
    # art. 242 nonies A CGI). Fige au moment du devis comme les autres infos client.
    client_tva_intracom: Mapped[str | None] = mapped_column(String(20))

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
    # Recurrent offert (deduit du mensuel facture : pack/options offerts en mensuel)
    total_offerts_recurrent_ht: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

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

    # Parametres specifiques au document (surtout Shopify / proposition budgetaire).
    # Stockes en JSON pour rester souple sans multiplier les colonnes : forfait
    # references produits, parametres de maintenance affiches, bloc frais externes,
    # etc. Cf. generation_devis._params() pour les cles lues.
    params_doc: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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
    documents: Mapped[list["DevisDocument"]] = relationship(
        back_populates="devis",
        cascade="all, delete-orphan",
        order_by="DevisDocument.id",
    )

    @property
    def est_shopify(self) -> bool:
        """Vrai si le devis porte sur une offre Shopify (vs Webflow).

        Source unique de la detection : pilote le wording "maintenance &
        exploitation" (Shopify, hebergement assure par la plateforme) vs
        "maintenance & hebergement" (Webflow), sur le devis comme sur la facture.
        """
        return "shopify" in (self.offre_type_site or "").lower()

    @property
    def libelle_support(self) -> str:
        """Designation du support cree, sans detail (nb de pages, nom d'offre) :
        'boutique en ligne' pour Shopify, 'site internet' sinon (Webflow)."""
        return "boutique en ligne" if self.est_shopify else "site internet"

    @property
    def libelle_creation(self) -> str:
        """Objet metier d'une facture de creation (acompte/solde) : decrit la
        nature de la prestation sans le nom commercial de l'offre ni le nombre de
        pages (qui devient faux des qu'on ajoute des pages en option)."""
        return f"Création d'une {self.libelle_support}" if self.est_shopify \
            else f"Création d'un {self.libelle_support}"


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
