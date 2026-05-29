"""Service de generation de references devis et factures.

Format devis :  D-XXXX-AAMMJJHHMM
Format facture: F-XXXX-AAMMJJHHMM-N

XXXX = 4 lettres derivees du nom de societe du client :
  - Supprime formes juridiques (SAS, SARL, SASU, etc.)
  - Supprime articles (Le, La, Les, L')
  - Supprime accents et caracteres speciaux
  - 1 mot  -> 4 premieres lettres (OMNI)
  - 2 mots -> 2 premieres de chaque (BLIN, AUTS)
  - 3+ mots -> 2 du 1er + 1 du 2e + 1 du 3e (ASFO)
  - Complete avec X si pas assez de lettres
"""

import re
import unicodedata
from datetime import datetime


# Formes juridiques a supprimer
_FORMES = {
    "SAS", "SASU", "SARL", "EURL", "SA", "SCI", "EI", "EIRL",
    "SELARL", "SNC", "SCP", "SEP", "GAEC", "EARL", "GIE", "SCEA",
    "AUTO-ENTREPRENEUR", "AUTOENTREPRENEUR", "ASSOCIATION",
}

# Articles a supprimer
_ARTICLES = {"LE", "LA", "LES", "L", "DE", "DES", "DU", "D", "ET"}


def _remove_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _extract_code(raison_sociale: str) -> str:
    """Extrait un code de 4 lettres a partir de la raison sociale."""
    # Normaliser
    text = _remove_accents(raison_sociale.upper().strip())

    # Garder seulement lettres et espaces
    text = re.sub(r"[^A-Z\s]", " ", text)

    # Decouper en mots
    words = text.split()

    # Supprimer formes juridiques et articles
    words = [w for w in words if w not in _FORMES and w not in _ARTICLES]

    if not words:
        return "XXXX"

    if len(words) == 1:
        # 1 mot : 4 premieres lettres
        code = words[0][:4]
    elif len(words) == 2:
        # 2 mots : 3 du 1er + 1 du 2e
        code = words[0][:3] + words[1][:1]
    else:
        # 3+ mots : 2 du 1er + 1 du 2e + 1 du 3e
        code = words[0][:2] + words[1][:1] + words[2][:1]

    # Completer avec X si trop court
    return code.ljust(4, "X")[:4]


def generer_reference_devis(raison_sociale: str, dt: datetime | None = None) -> str:
    """Genere une reference de devis : D-XXXX-AAMMJJHHMM."""
    if dt is None:
        dt = datetime.now()
    code = _extract_code(raison_sociale)
    ts = dt.strftime("%y%m%d%H%M")
    return f"D-{code}-{ts}"


def generer_reference_facture(
    raison_sociale: str, num_facture: int = 1, dt: datetime | None = None
) -> str:
    """Genere une reference de facture : F-XXXX-AAMMJJHHMM-N."""
    if dt is None:
        dt = datetime.now()
    code = _extract_code(raison_sociale)
    ts = dt.strftime("%y%m%d%H%M")
    return f"F-{code}-{ts}-{num_facture}"
