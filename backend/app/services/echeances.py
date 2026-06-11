"""Repartition d'un montant en echeances, exacte au centime.

Mutualise par le simulateur (apercu des prelevements) et la generation des
devis/factures (echeancier reel), pour qu'ils affichent toujours les memes
montants.
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

_CENT = Decimal("0.01")

# Delai de paiement maximal entre professionnels (B2B), art. L441-10 du Code de
# commerce : 60 jours a compter de l'emission de la facture. Sert de borne a
# l'etalement de l'echeancier : le dernier versement ne depasse pas la date de
# signature + 60 jours, de sorte que le paiement en plusieurs fois reste dans
# le temps imparti par la legislation.
DELAI_LEGAL_B2B_JOURS = 60


def _q(v) -> Decimal:
    return Decimal(v).quantize(_CENT, rounding=ROUND_HALF_UP)


def dates_echeancier(base: date, intervalle_jours: int, n: int) -> list[date]:
    """Pre-remplit n dates d'echeance : base, base+pas, base+2*pas, ...

    Le pas (intervalle en jours) tombe a 30 si invalide. Les dates restent
    modifiables ligne par ligne ensuite (echeancier editable).
    """
    pas = intervalle_jours if (intervalle_jours and intervalle_jours > 0) else 30
    return [base + timedelta(days=i * pas) for i in range(n)]


def dates_echeancier_legal(
    base: date, n: int, delai_max_jours: int = DELAI_LEGAL_B2B_JOURS
) -> list[date]:
    """Repartit n dates d'echeance regulierement entre `base` (1er versement, du
    a la signature) et `base + delai_max_jours` (dernier versement), afin que le
    paiement en plusieurs fois tienne dans le delai legal B2B.

    - n <= 1 : [base] (paiement comptant, du a la signature)
    - n  > 1 : base, base + pas, ..., base + delai_max_jours, avec un pas regulier
      egal a delai_max_jours / (n - 1).

    Exemples (delai 60 j) :
      3x -> J, J+30, J+60
      4x -> J, J+20, J+40, J+60

    Les dates restent modifiables ligne par ligne ensuite (echeancier editable).
    """
    if n <= 1:
        return [base]
    pas = delai_max_jours / (n - 1)
    return [base + timedelta(days=round(i * pas)) for i in range(n)]


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
