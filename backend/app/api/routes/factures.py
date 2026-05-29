"""Routes pour les factures."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.facture import Facture, StatutFacture, TypeFacture
from app.models.devis import Devis
from app.models.societe import Societe
from app.services.generation_facture import FactureData, generer_facture
from pydantic import BaseModel
from decimal import Decimal
from datetime import date

router = APIRouter()


class FactureSummary(BaseModel):
    id: int
    numero: str
    type: TypeFacture
    statut: StatutFacture
    date_emission: date
    date_echeance: date
    objet: str
    total_ttc: Decimal

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[FactureSummary])
async def list_factures(
    statut: StatutFacture | None = None,
    type: TypeFacture | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Facture).order_by(Facture.date_emission.desc())
    if statut:
        query = query.where(Facture.statut == statut)
    if type:
        query = query.where(Facture.type == type)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{facture_id}", response_model=FactureSummary)
async def get_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    return facture


@router.get("/{facture_id}/document")
async def telecharger_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Genere et retourne la facture au format Word (.docx)."""
    result = await db.execute(
        select(Facture)
        .where(Facture.id == facture_id)
        .options(selectinload(Facture.echeances), selectinload(Facture.lignes))
    )
    facture = result.scalar_one_or_none()
    if not facture:
        raise HTTPException(404, "Facture non trouvee")

    devis = await db.get(Devis, facture.devis_id)
    societe = (await db.execute(select(Societe).limit(1))).scalar_one_or_none()

    echeances = sorted(facture.echeances, key=lambda e: e.numero)
    ech_rows = [
        {"label": e.label, "date": e.date_echeance.strftime("%d/%m/%Y"), "ttc": e.montant_ttc}
        for e in echeances
    ]
    idx_echeance = sum(1 for e in echeances if e.payee)

    cp_ville = " ".join(x for x in [devis.client_cp, devis.client_ville] if x) if devis else ""

    data = FactureData(
        numero=facture.numero,
        type_facture=facture.type.value,
        date_emission=facture.date_emission,
        date_echeance=facture.date_echeance,
        objet=facture.objet,
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
        client_societe=devis.client_raison_sociale if devis else "",
        client_contact=devis.client_interlocuteur if devis else "",
        client_adresse=devis.client_adresse if devis else "",
        client_cp_ville=cp_ville,
        client_siret=devis.client_siret if devis else "",
        designation=facture.objet,
        quantite="1",
        prix_unitaire_ht=facture.total_ht,
        montant_ht=facture.total_ht,
        devis_ref=devis.reference if devis else "",
        echeances=ech_rows,
        idx_echeance=idx_echeance,
    )

    buf = generer_facture(data)
    filename = f"Facture_{facture.numero}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/next-numero", response_model=dict)
async def next_numero(db: AsyncSession = Depends(get_db)):
    """Genere le prochain numero de facture (F2026-XXX)."""
    year = date.today().year
    prefix = f"F{year}-"
    result = await db.execute(
        select(func.count()).where(Facture.numero.like(f"{prefix}%"))
    )
    count = result.scalar() or 0
    return {"numero": f"{prefix}{count + 1:03d}"}
