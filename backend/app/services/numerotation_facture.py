"""Numerotation legale des factures et avoirs : sequence chronologique continue.

Format du numero LEGAL (attribue a l'EMISSION, jamais au brouillon) :
  - Facture : F-XXXX-AAMMJJ-NNN   (ex F-ASKV-260415-001)
  - Avoir   : AV-XXXX-AAMMJJ-NNN  (ex AV-ASKV-260611-001)

  XXXX   = code 4 lettres du client (cf reference.code_client)
  AAMMJJ = date d'emission
  NNN    = compteur incremental CONTINU par annee (3 chiffres min), qui ne fait
           qu'augmenter -> sequence sans trou, comme l'exige l'art. 242 nonies A
           de l'annexe II au CGI. Le compteur FACTURE est commun a toutes les
           factures (acompte, solde, maintenance, prestation...). Les AVOIRS ont
           leur propre serie continue dediee (table compteur_avoir).

Un brouillon (numero provisoire horodate F-XXXX-AAMMJJHHMM-N) ne consomme aucun
numero : la sequence legale reste continue meme si un brouillon est supprime.
"""

from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def format_numero_facture(code: str, dt: date, n: int) -> str:
    """Numero legal de facture : F-XXXX-AAMMJJ-NNN (NNN sur 3 chiffres min)."""
    return f"F-{code}-{dt.strftime('%y%m%d')}-{n:03d}"


def format_numero_avoir(code: str, dt: date, n: int) -> str:
    """Numero d'avoir : AV-XXXX-AAMMJJ-NNN (NNN sur 3 chiffres min)."""
    return f"AV-{code}-{dt.strftime('%y%m%d')}-{n:03d}"


async def prochain_compteur_facture(db: AsyncSession, annee: int) -> int:
    """Increment atomique du compteur de factures de l'annee, renvoie le numero brut.

    UPSERT atomique (RETURNING) : aucun appel concurrent ne recoit le meme numero.
    """
    row = await db.execute(
        text(
            "INSERT INTO compteur_facture (annee, dernier) VALUES (:annee, 1) "
            "ON CONFLICT (annee) DO UPDATE SET dernier = compteur_facture.dernier + 1 "
            "RETURNING dernier"
        ),
        {"annee": annee},
    )
    return row.scalar_one()


async def prochain_compteur_avoir(db: AsyncSession, annee: int) -> int:
    """Increment atomique du compteur d'avoirs de l'annee (serie dediee continue)."""
    row = await db.execute(
        text(
            "INSERT INTO compteur_avoir (annee, dernier) VALUES (:annee, 1) "
            "ON CONFLICT (annee) DO UPDATE SET dernier = compteur_avoir.dernier + 1 "
            "RETURNING dernier"
        ),
        {"annee": annee},
    )
    return row.scalar_one()


async def numero_en_cours(db: AsyncSession, annee: int) -> int:
    """Dernier compteur de facture attribue pour l'annee (0 si aucun). Lecture seule."""
    row = await db.execute(
        text("SELECT dernier FROM compteur_facture WHERE annee = :annee"),
        {"annee": annee},
    )
    return row.scalar_one_or_none() or 0
