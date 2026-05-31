"""Service du journal des modifications sensibles.

Centralise l'ecriture des lignes d'historique (numeros, dates, echeancier)
pour les devis et factures. N'effectue pas de commit : c'est l'appelant qui
valide la transaction.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import JournalModification


def _str(val) -> str | None:
    if val is None:
        return None
    return str(val)


def enregistrer(
    db: AsyncSession, entite: str, entite_id: int, champ: str,
    ancienne, nouvelle, motif: str | None = None, auteur: str | None = None,
) -> None:
    """Ajoute une ligne d'historique a la session (commit gere par l'appelant)."""
    db.add(JournalModification(
        entite=entite, entite_id=entite_id, champ=champ,
        ancienne_valeur=_str(ancienne), nouvelle_valeur=_str(nouvelle),
        motif=motif, auteur=auteur,
    ))


async def historique(db: AsyncSession, entite: str, entite_id: int) -> list[dict]:
    """Retourne l'historique d'une entite, du plus recent au plus ancien."""
    rows = (await db.execute(
        select(JournalModification)
        .where(JournalModification.entite == entite,
               JournalModification.entite_id == entite_id)
        .order_by(JournalModification.cree_le.desc(), JournalModification.id.desc())
    )).scalars().all()
    return [
        {
            "id": r.id,
            "champ": r.champ,
            "ancienne_valeur": r.ancienne_valeur,
            "nouvelle_valeur": r.nouvelle_valeur,
            "motif": r.motif,
            "auteur": r.auteur,
            "cree_le": r.cree_le.isoformat() if r.cree_le else None,
        }
        for r in rows
    ]
