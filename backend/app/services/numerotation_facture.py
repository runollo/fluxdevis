"""Numerotation legale des factures : sequence chronologique continue par annee.

Le numero F<annee>-NNN est attribue a l'EMISSION d'une facture (passage du
brouillon a "emise"), JAMAIS a la creation du brouillon. Un brouillon supprime
ne consomme donc aucun numero : la sequence reste continue, sans trou, comme
l'exige l'art. 242 nonies A de l'annexe II au CGI.

Le compteur (table compteur_facture) ne fait qu'augmenter, par annee. NNN est
zero-padde sur 3 chiffres minimum (F2026-010), et s'etend au-dela si besoin.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def format_numero(annee: int, n: int) -> str:
    """Formate le numero legal : F<annee>-NNN (3 chiffres min)."""
    return f"F{annee}-{n:03d}"


async def prochain_numero(db: AsyncSession, annee: int) -> str:
    """Incremente atomiquement le compteur de l'annee et renvoie le numero legal.

    UPSERT atomique : si l'annee n'existe pas encore, elle est creee a 1 ;
    sinon `dernier` est incremente. Le RETURNING garantit qu'aucun appel
    concurrent ne recoit le meme numero (verrou de ligne PostgreSQL).
    """
    row = await db.execute(
        text(
            """
            INSERT INTO compteur_facture (annee, dernier)
            VALUES (:annee, 1)
            ON CONFLICT (annee)
            DO UPDATE SET dernier = compteur_facture.dernier + 1
            RETURNING dernier
            """
        ),
        {"annee": annee},
    )
    n = row.scalar_one()
    return format_numero(annee, n)


async def numero_en_cours(db: AsyncSession, annee: int) -> int:
    """Renvoie le dernier numero attribue pour l'annee (0 si aucun). Lecture seule."""
    row = await db.execute(
        text("SELECT dernier FROM compteur_facture WHERE annee = :annee"),
        {"annee": annee},
    )
    return row.scalar_one_or_none() or 0


def format_numero_avoir(annee: int, n: int) -> str:
    """Formate le numero d'avoir : AV<annee>-NNN (3 chiffres min)."""
    return f"AV{annee}-{n:03d}"


async def prochain_numero_avoir(db: AsyncSession, annee: int) -> str:
    """Increment atomique du compteur d'avoirs de l'annee, renvoie AV<annee>-NNN.

    Sequence distincte des factures (table compteur_avoir).
    """
    row = await db.execute(
        text(
            """
            INSERT INTO compteur_avoir (annee, dernier)
            VALUES (:annee, 1)
            ON CONFLICT (annee)
            DO UPDATE SET dernier = compteur_avoir.dernier + 1
            RETURNING dernier
            """
        ),
        {"annee": annee},
    )
    n = row.scalar_one()
    return format_numero_avoir(annee, n)
