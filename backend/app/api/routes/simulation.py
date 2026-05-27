"""Route API pour la simulation de prix."""

from decimal import Decimal
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.simulation import (
    SimulationInput, PrestationSurMesure, SelectionOption,
    ArticleOffert, SimulationResult, simuler,
)

router = APIRouter()

D = Decimal


class PrestationIn(BaseModel):
    designation: str = ""
    quantite: int = 0
    prix_unitaire_achat: Decimal = D("0")
    prix_unitaire_vente: Decimal = D("0")


class SelectionIn(BaseModel):
    option_id: int = 0
    code: str = ""
    nom: str = ""
    type_ligne: str = ""
    quantite: int = 0
    statut: str = ""
    prix_achat_setup: Decimal = D("0")
    prix_vente_setup: Decimal = D("0")
    prix_achat_mensuel: Decimal = D("0")
    prix_vente_mensuel: Decimal = D("0")


class ArticleOffertIn(BaseModel):
    designation: str = ""
    prix_achat: Decimal = D("0")
    prix_vente: Decimal = D("0")
    est_setup: bool = True


class SimulationRequest(BaseModel):
    offre_nom: str = ""
    offre_type_site: str = ""
    prix_achat: Decimal = D("0")
    prix_vente_conseille: Decimal = D("0")
    mode_reglement: str = "Comptant"
    duree_financement: str = ""
    coefficient_locam: Decimal = D("0")
    pct_maintenance_locam: Decimal = D("0")
    garantie_web: Decimal = D("10")
    prestations: list[PrestationIn] = []
    selections: list[SelectionIn] = []
    articles_offerts: list[ArticleOffertIn] = []
    remise_pct_setup: Decimal = D("0")
    remise_pct_recurrent: Decimal = D("0")
    marge_additionnelle: Decimal = D("0")
    plan_paiement: str = "100%"
    mode_prix_setup: str = "Net"
    mode_prix_recurrent: str = "Net"
    prix_setup_personnalise: Decimal = D("0")
    prix_mensuel_personnalise: Decimal = D("0")


class SimulationResponse(BaseModel):
    prix_vente_final: Decimal
    prix_setup_affiche: Decimal
    prix_mensuel_affiche: Decimal
    total_setup_ht: Decimal
    total_setup_tva: Decimal
    total_setup_ttc: Decimal
    total_mensuel_ht: Decimal
    total_mensuel_tva: Decimal
    total_mensuel_ttc: Decimal
    total_prestations_vente: Decimal
    total_options_setup_vente: Decimal
    total_pack_maintenance_vente: Decimal
    total_options_recurrent_vente: Decimal
    remise_eur_setup: Decimal
    remise_eur_recurrent: Decimal
    marge: Decimal
    marge_totale: Decimal
    # Leasing
    montant_finance: Decimal
    loyer: Decimal
    loyer_client_ht: Decimal
    # Comptant
    prelevement_1: Decimal
    prelevement_2: Decimal
    prelevement_3: Decimal
    prelevement_4: Decimal
    recurrent_mensuel: Decimal


@router.post("/", response_model=SimulationResponse)
async def run_simulation(req: SimulationRequest):
    """Lance une simulation de prix et retourne les resultats."""
    inp = SimulationInput(
        offre_nom=req.offre_nom,
        offre_type_site=req.offre_type_site,
        prix_achat=req.prix_achat,
        prix_vente_conseille=req.prix_vente_conseille,
        mode_reglement=req.mode_reglement,
        duree_financement=req.duree_financement,
        coefficient_locam=req.coefficient_locam,
        pct_maintenance_locam=req.pct_maintenance_locam,
        garantie_web=req.garantie_web,
        prestations=[PrestationSurMesure(**p.model_dump()) for p in req.prestations],
        selections=[SelectionOption(**s.model_dump()) for s in req.selections],
        articles_offerts=[ArticleOffert(**a.model_dump()) for a in req.articles_offerts],
        remise_pct_setup=req.remise_pct_setup,
        remise_pct_recurrent=req.remise_pct_recurrent,
        marge_additionnelle=req.marge_additionnelle,
        plan_paiement=req.plan_paiement,
        mode_prix_setup=req.mode_prix_setup,
        mode_prix_recurrent=req.mode_prix_recurrent,
        prix_setup_personnalise=req.prix_setup_personnalise,
        prix_mensuel_personnalise=req.prix_mensuel_personnalise,
    )
    r = simuler(inp)
    return SimulationResponse(
        prix_vente_final=r.prix_vente_final,
        prix_setup_affiche=r.prix_setup_affiche,
        prix_mensuel_affiche=r.prix_mensuel_affiche,
        total_setup_ht=r.total_setup_ht,
        total_setup_tva=r.total_setup_tva,
        total_setup_ttc=r.total_setup_ttc,
        total_mensuel_ht=r.total_mensuel_ht,
        total_mensuel_tva=r.total_mensuel_tva,
        total_mensuel_ttc=r.total_mensuel_ttc,
        total_prestations_vente=r.total_prestations_vente,
        total_options_setup_vente=r.total_options_setup_vente,
        total_pack_maintenance_vente=r.total_pack_maintenance_vente,
        total_options_recurrent_vente=r.total_options_recurrent_vente,
        remise_eur_setup=r.remise_eur_setup,
        remise_eur_recurrent=r.remise_eur_recurrent,
        marge=r.marge,
        marge_totale=r.marge_totale,
        montant_finance=r.montant_finance,
        loyer=r.loyer,
        loyer_client_ht=r.loyer_client_ht,
        prelevement_1=r.prelevement_1,
        prelevement_2=r.prelevement_2,
        prelevement_3=r.prelevement_3,
        prelevement_4=r.prelevement_4,
        recurrent_mensuel=r.recurrent_mensuel,
    )
