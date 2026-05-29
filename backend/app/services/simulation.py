"""Service de simulation — logique de calcul portee depuis simu_live.py v8.1.

Toute la logique metier du simulateur Excel en Python pur,
sans dependance a openpyxl. Arithmetique Decimal pour la precision comptable.
"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from fractions import Fraction
import re

from app.services.echeances import repartir_au_centime

D = Decimal

# Fractions exactes de chaque plan de paiement comptant (cf. echeances.py)
_PLAN_FRACTIONS = {
    "100%": [Fraction(1, 1)],
    "50/50": [Fraction(1, 2), Fraction(1, 2)],
    "33/33/33": [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)],
    "50/25/25": [Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)],
    "25/25/25/25": [Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4)],
}


def _q(val) -> Decimal:
    """Arrondi comptable a 2 decimales."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Structures de donnees
# ---------------------------------------------------------------------------

@dataclass
class PrestationSurMesure:
    designation: str = ""
    quantite: int = 0
    prix_unitaire_achat: Decimal = D("0")
    prix_unitaire_vente: Decimal = D("0")


@dataclass
class SelectionOption:
    option_id: int = 0
    code: str = ""
    nom: str = ""
    type_ligne: str = ""  # OPTION_SETUP, OPTION_RECURRENT, PACK
    quantite: int = 0
    statut: str = ""  # Inclus, Option payante, Non disponible, etc.
    prix_achat_setup: Decimal = D("0")
    prix_vente_setup: Decimal = D("0")
    prix_achat_mensuel: Decimal = D("0")
    prix_vente_mensuel: Decimal = D("0")


@dataclass
class ArticleOffert:
    designation: str = ""
    prix_achat: Decimal = D("0")
    prix_vente: Decimal = D("0")
    est_setup: bool = True  # True=setup, False=recurrent


@dataclass
class SimulationInput:
    # Offre
    offre_nom: str = ""
    offre_type_site: str = ""
    prix_achat: Decimal = D("0")
    prix_vente_conseille: Decimal = D("0")

    # Mode
    mode_reglement: str = "Comptant"  # Comptant / Leasing

    # Leasing
    duree_financement: str = ""
    coefficient_locam: Decimal = D("0")
    pct_maintenance_locam: Decimal = D("0")
    garantie_web: Decimal = D("10")

    # Prestations sur mesure (3 max)
    prestations: list[PrestationSurMesure] = field(default_factory=list)

    # Options selectionnees
    selections: list[SelectionOption] = field(default_factory=list)

    # Articles offerts (5 max)
    articles_offerts: list[ArticleOffert] = field(default_factory=list)

    # Remises
    remise_pct_setup: Decimal = D("0")
    remise_pct_recurrent: Decimal = D("0")

    # Marge additionnelle
    marge_additionnelle: Decimal = D("0")

    # Plan de paiement (Comptant)
    plan_paiement: str = "100%"

    # Devis params
    mode_prix_setup: str = "Net"
    mode_prix_recurrent: str = "Net"
    prix_setup_personnalise: Decimal = D("0")
    prix_mensuel_personnalise: Decimal = D("0")


@dataclass
class SimulationResult:
    # Totaux options
    total_prestations_achat: Decimal = D("0")
    total_prestations_vente: Decimal = D("0")
    total_options_setup_achat: Decimal = D("0")
    total_options_setup_vente: Decimal = D("0")
    total_pack_maintenance_achat: Decimal = D("0")
    total_pack_maintenance_vente: Decimal = D("0")
    total_options_recurrent_achat: Decimal = D("0")
    total_options_recurrent_vente: Decimal = D("0")

    # Articles offerts ventiles
    offerts_setup_vente: Decimal = D("0")
    offerts_setup_achat: Decimal = D("0")
    offerts_recurrent_vente: Decimal = D("0")

    # Remises EUR
    remise_eur_setup: Decimal = D("0")
    remise_eur_recurrent: Decimal = D("0")

    # Prix
    prix_vente_final: Decimal = D("0")

    # Zone Q
    prix_setup_catalogue: Decimal = D("0")
    prix_mensuel_catalogue: Decimal = D("0")
    prix_setup_net: Decimal = D("0")
    prix_mensuel_net: Decimal = D("0")
    prix_setup_affiche: Decimal = D("0")
    prix_mensuel_affiche: Decimal = D("0")

    # Marge
    marge: Decimal = D("0")
    marge_totale: Decimal = D("0")

    # Leasing
    n_mois: int = 0
    is_quarterly: bool = False
    montant_finance: Decimal = D("0")
    loyer: Decimal = D("0")
    maintenance_reversee: Decimal = D("0")
    loyer_client_ht: Decimal = D("0")

    # Plan paiement comptant
    prelevement_1: Decimal = D("0")
    prelevement_2: Decimal = D("0")
    prelevement_3: Decimal = D("0")
    prelevement_4: Decimal = D("0")
    recurrent_mensuel: Decimal = D("0")

    # Totaux TTC
    total_setup_ht: Decimal = D("0")
    total_setup_tva: Decimal = D("0")
    total_setup_ttc: Decimal = D("0")
    total_mensuel_ht: Decimal = D("0")
    total_mensuel_tva: Decimal = D("0")
    total_mensuel_ttc: Decimal = D("0")


# ---------------------------------------------------------------------------
# Moteur de calcul
# ---------------------------------------------------------------------------

def extract_n_mois(duree_str: str) -> tuple[int, bool]:
    """Extrait le nombre de mois et si c'est trimestriel."""
    if not duree_str:
        return 0, False
    if " T" in duree_str:
        match = re.search(r"(\d+)\s+T", duree_str)
        return (int(match.group(1)) * 3 if match else 0), True
    match = re.search(r"(\d+)", duree_str)
    return (int(match.group(1)) if match else 0), False


def _sum_by_type(sels: list[SelectionOption], type_l: str, attr: str) -> Decimal:
    """Somme les options d'un type donne (hors Inclus/Non disponible)."""
    total = D("0")
    for s in sels:
        if s.type_ligne == type_l and s.statut not in ("Inclus", "Non disponible") and s.quantite >= 1:
            total += getattr(s, attr) * s.quantite
    return total


def simuler(inp: SimulationInput) -> SimulationResult:
    """Execute la simulation complete."""
    r = SimulationResult()
    mode = inp.mode_reglement

    # Nombre de mois
    r.n_mois, r.is_quarterly = extract_n_mois(inp.duree_financement)

    # Prestations sur mesure (ligne 19)
    for p in inp.prestations:
        r.total_prestations_achat += p.quantite * p.prix_unitaire_achat
        r.total_prestations_vente += p.quantite * p.prix_unitaire_vente

    # Totaux options par type (lignes 21-23)
    r.total_options_setup_achat = _sum_by_type(inp.selections, "OPTION_SETUP", "prix_achat_setup")
    r.total_options_setup_vente = _sum_by_type(inp.selections, "OPTION_SETUP", "prix_vente_setup")
    r.total_pack_maintenance_achat = _sum_by_type(inp.selections, "PACK", "prix_achat_mensuel")
    r.total_pack_maintenance_vente = _sum_by_type(inp.selections, "PACK", "prix_vente_mensuel")
    r.total_options_recurrent_achat = _sum_by_type(inp.selections, "OPTION_RECURRENT", "prix_achat_mensuel")
    r.total_options_recurrent_vente = _sum_by_type(inp.selections, "OPTION_RECURRENT", "prix_vente_mensuel")

    # Articles offerts ventilation (ligne 46)
    total_offerts_vente = D("0")
    total_offerts_achat = D("0")
    for a in inp.articles_offerts:
        if not a.designation:
            continue
        total_offerts_vente += a.prix_vente
        total_offerts_achat += a.prix_achat
        if a.est_setup:
            r.offerts_setup_vente += a.prix_vente
            r.offerts_setup_achat += a.prix_achat
    r.offerts_recurrent_vente = total_offerts_vente - r.offerts_setup_vente

    # Remises EUR (ligne 45)
    if mode == "Leasing":
        base_setup = inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente - total_offerts_vente
        base_recurrent = r.total_pack_maintenance_vente + r.total_options_recurrent_vente
    else:
        base_setup = inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente - r.offerts_setup_vente
        base_recurrent = r.total_pack_maintenance_vente + r.total_options_recurrent_vente - r.offerts_recurrent_vente
    r.remise_eur_setup = _q(inp.remise_pct_setup * base_setup)
    r.remise_eur_recurrent = _q(inp.remise_pct_recurrent * base_recurrent)

    # Prix de vente final (F12)
    if mode == "Leasing":
        r.prix_vente_final = _q(
            inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente
            + inp.marge_additionnelle - total_offerts_vente - r.remise_eur_setup
        )
    else:
        r.prix_vente_final = _q(
            inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente
            + inp.marge_additionnelle - r.offerts_setup_vente - r.remise_eur_setup
        )

    # Zone Q
    r.prix_setup_catalogue = _q(
        inp.prix_vente_conseille + r.total_prestations_vente
        + r.total_options_setup_vente + inp.marge_additionnelle
    )
    r.prix_mensuel_catalogue = _q(r.total_pack_maintenance_vente + r.total_options_recurrent_vente)
    r.prix_setup_net = r.prix_vente_final
    if mode == "Leasing":
        r.prix_mensuel_net = _q(
            (r.total_pack_maintenance_vente + r.total_options_recurrent_vente)
            * (1 - inp.remise_pct_recurrent) - r.offerts_recurrent_vente
        )
    else:
        r.prix_mensuel_net = _q(
            (r.total_pack_maintenance_vente + r.total_options_recurrent_vente - r.offerts_recurrent_vente)
            * (1 - inp.remise_pct_recurrent)
        )
    _s_map = {"Catalogue": r.prix_setup_catalogue, "Net": r.prix_setup_net, "Personnalise": inp.prix_setup_personnalise}
    _m_map = {"Catalogue": r.prix_mensuel_catalogue, "Net": r.prix_mensuel_net, "Personnalise": inp.prix_mensuel_personnalise}
    r.prix_setup_affiche = _s_map.get(inp.mode_prix_setup, r.prix_setup_net)
    r.prix_mensuel_affiche = _m_map.get(inp.mode_prix_recurrent, r.prix_mensuel_net)

    # Marge (ligne 31)
    if mode == "Leasing":
        one_shot = (
            (inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente)
            - total_offerts_vente - r.remise_eur_setup
            - (inp.prix_achat + r.total_prestations_achat + r.total_options_setup_achat - total_offerts_achat)
        )
        recurrent = (
            (r.total_pack_maintenance_vente + r.total_options_recurrent_vente) * (1 - inp.remise_pct_recurrent)
            - (r.total_pack_maintenance_achat + r.total_options_recurrent_achat)
        ) * r.n_mois
    else:
        one_shot = (
            (inp.prix_vente_conseille + r.total_prestations_vente + r.total_options_setup_vente)
            - r.offerts_setup_vente - r.remise_eur_setup
            - (inp.prix_achat + r.total_prestations_achat + r.total_options_setup_achat - r.offerts_setup_achat)
        )
        recurrent = (
            (r.total_pack_maintenance_vente + r.total_options_recurrent_vente - r.offerts_recurrent_vente)
            * (1 - inp.remise_pct_recurrent)
            - (r.total_pack_maintenance_achat + r.total_options_recurrent_achat
               - (total_offerts_achat - r.offerts_setup_achat))
        )
    r.marge = _q(one_shot + recurrent)
    r.marge_totale = _q(r.marge + inp.marge_additionnelle)

    # Leasing (lignes 35-39)
    if mode == "Leasing" and r.n_mois > 0 and inp.coefficient_locam > 0:
        numerator = (
            r.prix_vente_final
            + (r.total_pack_maintenance_vente + r.total_options_recurrent_vente)
            * (1 - inp.remise_pct_recurrent) * r.n_mois
        )
        denominator = 1 + (inp.coefficient_locam / 100) * inp.pct_maintenance_locam * r.n_mois
        r.montant_finance = _q(numerator / denominator)
        factor = 3 if r.is_quarterly else 1
        r.loyer = _q(r.montant_finance * (inp.coefficient_locam / 100) * factor)
        r.maintenance_reversee = _q(r.loyer * inp.pct_maintenance_locam)
        r.loyer_client_ht = _q(r.loyer * (1 + inp.pct_maintenance_locam) + inp.garantie_web * factor)

    # Totaux TTC (calcules avant les prelevements pour servir de base TTC)
    tva = D("0.20")
    r.total_setup_ht = r.prix_setup_affiche
    r.total_setup_tva = _q(r.total_setup_ht * tva)
    r.total_setup_ttc = _q(r.total_setup_ht + r.total_setup_tva)
    r.total_mensuel_ht = r.prix_mensuel_affiche
    r.total_mensuel_tva = _q(r.total_mensuel_ht * tva)
    r.total_mensuel_ttc = _q(r.total_mensuel_ht + r.total_mensuel_tva)

    # Plan paiement comptant : prelevements exacts au centime sur le TOTAL SETUP
    # TTC (meme base que l'echeancier du devis/facture), ecart sur le 1er versement.
    if mode == "Comptant":
        montants = repartir_au_centime(
            r.total_setup_ttc, _PLAN_FRACTIONS.get(inp.plan_paiement, [Fraction(1, 1)])
        )
        for i, montant in enumerate(montants, start=1):
            setattr(r, f"prelevement_{i}", montant)
        r.recurrent_mensuel = _q(r.total_pack_maintenance_vente + r.total_options_recurrent_vente)

    return r
