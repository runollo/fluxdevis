"""Route API pour la generation de documents Word."""

from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.societe import Societe
from app.services.generation_facture import FactureData, generer_facture

router = APIRouter()


class GenererFactureRequest(BaseModel):
    numero: str
    type_facture: str = "acompte"  # acompte / maintenance
    date_emission: date
    date_echeance: date
    objet: str
    # Client
    client_societe: str
    client_contact: str = ""
    client_adresse: str = ""
    client_cp_ville: str = ""
    client_siret: str = ""
    client_email: str = ""
    # Ligne
    designation: str
    quantite: str = "1"
    prix_unitaire_ht: Decimal
    montant_ht: Decimal
    # Refs
    devis_ref: str = ""
    prestation: str = ""
    periode: str | None = None
    # Echeancier
    echeances: list[dict] = []
    idx_echeance: int = 0


@router.post("/facture")
async def generer_facture_endpoint(
    req: GenererFactureRequest,
    db: AsyncSession = Depends(get_db),
):
    """Genere une facture Word et la retourne en telechargement."""
    from sqlalchemy import select
    result = await db.execute(select(Societe).limit(1))
    societe = result.scalar_one_or_none()

    data = FactureData(
        numero=req.numero,
        type_facture=req.type_facture,
        date_emission=req.date_emission,
        date_echeance=req.date_echeance,
        objet=req.objet,
        emetteur_nom=societe.nom if societe else "BLUELINK INNOVATIONS",
        emetteur_forme=societe.forme_juridique if societe else "",
        emetteur_marque=societe.marque if societe else "FluXweb",
        emetteur_adresse=societe.adresse if societe else "",
        emetteur_cp_ville=societe.cp_ville if societe else "",
        emetteur_siret=societe.siret if societe else "",
        emetteur_rcs=societe.rcs if societe else "",
        emetteur_tva_num=societe.tva_intracom if societe else "",
        emetteur_email=societe.email if societe else "",
        emetteur_web=societe.site_web if societe else "",
        emetteur_iban=societe.iban if societe else "",
        emetteur_bic=societe.bic if societe else "",
        client_societe=req.client_societe,
        client_contact=req.client_contact,
        client_adresse=req.client_adresse,
        client_cp_ville=req.client_cp_ville,
        client_siret=req.client_siret,
        client_email=req.client_email,
        designation=req.designation,
        quantite=req.quantite,
        prix_unitaire_ht=req.prix_unitaire_ht,
        montant_ht=req.montant_ht,
        devis_ref=req.devis_ref,
        prestation=req.prestation,
        periode=req.periode,
        echeances=req.echeances,
        idx_echeance=req.idx_echeance,
    )

    buf = generer_facture(data)
    filename = f"Facture_{req.numero}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
