"""Repartition d'un montant en echeances, exacte au centime.

Mutualise par le simulateur (apercu des prelevements) et la generation des
devis/factures (echeancier reel), pour qu'ils affichent toujours les memes
montants.
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

_CENT = Decimal("0.01")


def _q(v) -> Decimal:
    return Decimal(v).quantize(_CENT, rounding=ROUND_HALF_UP)


def dates_echeancier(base: date, intervalle_jours: int, n: int) -> list[date]:
    """Pre-remplit n dates d'echeance : base, base+pas, base+2*pas, ...

    Le pas (intervalle en jours) tombe a 30 si invalide. Les dates restent
    modifiables ligne par ligne ensuite (echeancier editable).
    """
    pas = intervalle_jours if (intervalle_jours and intervalle_jours > 0) else 30
    return [base + timedelta(days=i * pas) for i in range(n)]


def repartir_au_centime(total, fractions: list[Fraction]) -> list[Decimal]:
    """Repartit `total` selon `fractions`, arrondi au centime.

    La somme des montants retournes vaut EXACTEMENT `total` : l'ecart d'arrondi
    (positif ou negatif) est porte par le PREMIER versement, afin que les
    versements suivants restent a leur montant nominal arrondi.

    Exemple : 3612,92 reparti en [1/3, 1/3, 1/3] -> [1204,30, 1204,31, 1204,31]
    (1204,31 x 3 ferait 3612,93, soit un centime de trop ; on retire ce centime
    du premier versement).
    """
    total = _q(total)
    montants = [
        _q(total * Decimal(f.numerator) / Decimal(f.denominator)) for f in fractions
    ]
    ecart = total - sum(montants)
    montants[0] = _q(montants[0] + ecart)
    return montants
