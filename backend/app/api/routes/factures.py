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
from app.services.facturation_maintenance import devis_maintenance_dus
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime, timezone

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
    archives: bool = False,
    q: str | None = None,
    skip: int = 0,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    """Liste les factures. Par defaut, exclut les factures archivees (corbeille).

    - archives=true : retourne uniquement les factures archivees.
    - q : recherche sur le numero ou l'objet (insensible a la casse).
    - skip / limit : pagination par decalage.
    """
    query = select(Facture).order_by(Facture.date_emission.desc(), Facture.id.desc())
    if archives:
        query = query.where(Facture.archived_at.is_not(None))
    else:
        query = query.where(Facture.archived_at.is_(None))
    if statut:
        query = query.where(Facture.statut == statut)
    if type:
        query = query.where(Facture.type == type)
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(Facture.numero.ilike(motif) | Facture.objet.ilike(motif))
    query = query.offset(max(skip, 0)).limit(max(min(limit, 200), 1))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/maintenance/dus")
async def maintenance_dus(db: AsyncSession = Depends(get_db)):
    """Liste les factures de maintenance dues aujourd'hui (pour automatisation Make/cron).

    Ne cree rien : retourne les devis a facturer avec la periode concernee. Une
    automatisation peut ensuite appeler POST /api/devis/{id}/factures-maintenance.
    """
    return await devis_maintenance_dus(db)


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

    periode = None
    if facture.type == TypeFacture.MAINTENANCE and facture.periode_debut and facture.periode_fin:
        periode = f"{facture.periode_debut.strftime('%d/%m/%Y')} au {facture.periode_fin.strftime('%d/%m/%Y')}"

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
        periode=periode,
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


@router.delete("/{facture_id}", status_code=204)
async def archiver_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Archive une facture (corbeille).

    Garde-fou juridique : SEULE une facture en brouillon (jamais emise) peut
    etre archivee. Une facture emise/payee/en retard ne se supprime pas — elle
    doit etre annulee par un avoir (POST /{id}/annuler), ce qui preserve la
    numerotation sequentielle imposee par l'administration fiscale.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.archived_at is not None:
        raise HTTPException(400, "Facture deja archivee")
    if facture.statut != StatutFacture.BROUILLON:
        raise HTTPException(
            400,
            "Une facture emise ne peut pas etre supprimee (numerotation legale). "
            "Utilisez l'annulation (avoir) a la place.",
        )
    facture.archived_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{facture_id}/annuler", response_model=FactureSummary)
async def annuler_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Annule une facture emise (equivalent avoir) : statut ANNULEE.

    La facture reste en base avec son numero — conformite : la numerotation
    sequentielle ne doit jamais comporter de trou. Une facture deja annulee ou
    deja en brouillon n'a pas a etre annulee.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.statut == StatutFacture.ANNULEE:
        raise HTTPException(400, "Facture deja annulee")
    if facture.statut == StatutFacture.BROUILLON:
        raise HTTPException(
            400,
            "Une facture en brouillon n'a pas a etre annulee : supprimez-la (corbeille).",
        )
    facture.statut = StatutFacture.ANNULEE
    await db.commit()
    await db.refresh(facture)
    return facture


@router.post("/{facture_id}/restaurer", response_model=FactureSummary)
async def restaurer_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Restaure une facture archivee (la sort de la corbeille)."""
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    facture.archived_at = None
    await db.commit()
    await db.refresh(facture)
    return facture
