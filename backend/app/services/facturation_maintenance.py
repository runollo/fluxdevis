"""Facturation du recurrent (maintenance / abonnement mensuel).

Independante du plan de paiement du setup : la maintenance demarre a la
mise en ligne du site (devis.date_mise_en_ligne) et se facture par periode
mensuelle glissante (anniversaire de la mise en ligne, sans prorata).

La logique est isolee ici pour etre reutilisable :
- par l'API (generation a la demande depuis le frontend) ;
- plus tard par une automatisation (cron interne, scenario Make en HTTP, ou
  envoi d'email via Resend) : `devis_maintenance_dus()` liste ce qui est a
  facturer, `generer_facture_maintenance()` cree la facture suivante.

Le leasing est volontairement exclu : en "tout inclus" la maintenance est
geree par le leaser, pas facturee au client (a traiter au premier contrat).
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.devis import Devis, ModeReglement
from app.models.facture import Facture, FactureLigne, TypeFacture, StatutFacture
from app.services.reference import generer_reference_facture

TVA = Decimal("0.20")


class MaintenanceError(Exception):
    """Erreur metier empechant la generation d'une facture de maintenance."""


def _q(val) -> Decimal:
    return Decimal(str(val or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ajouter_mois(d: date, k: int) -> date:
    """Ajoute k mois a une date en bornant le jour au dernier jour du mois cible."""
    total = d.month - 1 + k
    annee = d.year + total // 12
    mois = total % 12 + 1
    dernier_jour = calendar.monthrange(annee, mois)[1]
    return date(annee, mois, min(d.day, dernier_jour))


def periode_pour_index(mise_en_ligne: date, index: int) -> tuple[date, date]:
    """Periode mensuelle glissante n (0-indexee) depuis la mise en ligne.

    Index 0 : [mise_en_ligne ; mise_en_ligne + 1 mois - 1 jour]
    """
    debut = ajouter_mois(mise_en_ligne, index)
    fin = ajouter_mois(mise_en_ligne, index + 1) - timedelta(days=1)
    return debut, fin


def montant_recurrent_ht(devis: Devis) -> Decimal:
    """Montant HT mensuel du recurrent (pack maintenance + options recurrentes)."""
    return _q(devis.total_pack_maintenance_ht) + _q(devis.total_options_recurrent_ht)


async def _nb_factures(db: AsyncSession, devis_id: int, type_facture=None) -> int:
    query = select(func.count()).select_from(Facture).where(Facture.devis_id == devis_id)
    if type_facture is not None:
        query = query.where(Facture.type == type_facture)
    return (await db.execute(query)).scalar() or 0


async def prochaine_periode(
    db: AsyncSession, devis: Devis, today: date | None = None
) -> dict | None:
    """Retourne la prochaine periode de maintenance a facturer, ou None.

    None si : leasing, pas de mise en ligne, pas de recurrent, ou si la
    prochaine periode n'a pas encore commence (start > today).
    """
    today = today or date.today()
    if devis.mode_reglement == ModeReglement.LEASING:
        return None
    if not devis.date_mise_en_ligne:
        return None
    if montant_recurrent_ht(devis) <= 0:
        return None

    index = await _nb_factures(db, devis.id, TypeFacture.MAINTENANCE)
    debut, fin = periode_pour_index(devis.date_mise_en_ligne, index)
    if debut > today:
        return None  # periode future : on ne facture pas d'avance

    ht = montant_recurrent_ht(devis)
    return {
        "index": index,
        "debut": debut,
        "fin": fin,
        "montant_ht": ht,
        "montant_ttc": _q(ht * (Decimal("1") + TVA)),
    }


async def generer_facture_maintenance(
    db: AsyncSession, devis: Devis, today: date | None = None
) -> Facture:
    """Cree la facture de maintenance de la prochaine periode due. Commit inclus.

    Leve MaintenanceError avec un code explicite si la generation est impossible.
    """
    today = today or date.today()
    if devis.mode_reglement == ModeReglement.LEASING:
        raise MaintenanceError("Maintenance en leasing geree par le leaser (a venir)")
    if not devis.date_mise_en_ligne:
        raise MaintenanceError("Renseignez d'abord la date de mise en ligne du site")
    ht = montant_recurrent_ht(devis)
    if ht <= 0:
        raise MaintenanceError("Ce devis n'a pas de montant recurrent (maintenance)")

    index = await _nb_factures(db, devis.id, TypeFacture.MAINTENANCE)
    debut, fin = periode_pour_index(devis.date_mise_en_ligne, index)
    if debut > today:
        raise MaintenanceError(
            f"La prochaine periode (a partir du {debut:%d/%m/%Y}) n'a pas encore commence"
        )

    tva = _q(ht * TVA)
    ttc = ht + tva
    # Suffixe de numero base sur le total des factures du devis (unicite)
    total_factures = await _nb_factures(db, devis.id)
    numero = generer_reference_facture(devis.client_raison_sociale, num_facture=total_factures + 1)
    objet = (
        f"Maintenance {devis.offre_nom} — periode du "
        f"{debut:%d/%m/%Y} au {fin:%d/%m/%Y}"
    )

    ligne = FactureLigne(
        ordre=0, designation=objet, quantite=1,
        prix_unitaire_ht=ht, taux_tva=TVA, montant_ht=ht,
    )
    facture = Facture(
        numero=numero,
        type=TypeFacture.MAINTENANCE,
        statut=StatutFacture.BROUILLON,
        devis_id=devis.id,
        date_emission=today,
        date_echeance=today,
        periode_debut=debut,
        periode_fin=fin,
        objet=objet,
        total_ht=ht,
        total_tva=tva,
        total_ttc=ttc,
        lignes=[ligne],
    )
    db.add(facture)
    await db.commit()
    await db.refresh(facture)
    return facture


async def devis_maintenance_dus(db: AsyncSession, today: date | None = None) -> list[dict]:
    """Liste les devis dont une facture de maintenance est due aujourd'hui.

    Point d'entree pour l'automatisation (cron / Make / Resend) : retourne pour
    chaque devis concerne la periode a facturer. Ne cree rien.
    """
    today = today or date.today()
    result = await db.execute(
        select(Devis).where(
            Devis.date_mise_en_ligne.is_not(None),
            Devis.mode_reglement != ModeReglement.LEASING,
            Devis.archived_at.is_(None),
        )
    )
    dus: list[dict] = []
    for devis in result.scalars().all():
        periode = await prochaine_periode(db, devis, today=today)
        if periode is None:
            continue
        dus.append({
            "devis_id": devis.id,
            "reference": devis.reference,
            "client_raison_sociale": devis.client_raison_sociale,
            "client_email": devis.client_email,
            "periode_debut": periode["debut"].isoformat(),
            "periode_fin": periode["fin"].isoformat(),
            "montant_ttc": str(periode["montant_ttc"]),
        })
    return dus
