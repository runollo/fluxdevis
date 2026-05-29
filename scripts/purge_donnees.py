"""Purge des donnees de test (devis et factures) de la base FluxDevis.

ATTENTION : destruction physique reelle, reservee au DEVELOPPEMENT / aux TESTS.
Ce script vide entierement les documents (devis, factures et toutes leurs lignes)
pour repartir d'une base propre. Il NE TOUCHE PAS au catalogue (offres, options),
aux clients ni a la societe.

En production, on ne supprime jamais une facture emise : on la met a la corbeille
(archivage) ou on l'annule par un avoir, via l'interface. Ce script existe uniquement
pour ne pas polluer la base pendant les phases de test.

Usage:
    cd /home/ullop/.openclaw/workspace/projects/fluxdevis
    python scripts/purge_donnees.py          # demande confirmation
    python scripts/purge_donnees.py --force   # sans confirmation (cron/CI)
"""

import sys
import os

# Ajouter le backend au path pour les imports app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import text

from app.core.database import sync_engine

# Tables documentaires a vider. RESTART IDENTITY remet les sequences a 1,
# CASCADE vide automatiquement les tables enfants (lignes, echeances, options).
TABLES = ("devis", "factures")


def _compter(conn) -> dict[str, int]:
    counts = {}
    for tbl in ("devis", "factures", "devis_lignes", "devis_option_lignes",
                "devis_articles_offerts", "facture_lignes", "echeances"):
        counts[tbl] = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
    return counts


def purger() -> None:
    with sync_engine.connect() as conn:
        avant = _compter(conn)

    total = avant["devis"] + avant["factures"]
    print("Etat actuel des documents :")
    for tbl, n in avant.items():
        print(f"  {tbl:<24} {n}")

    if total == 0:
        print("\nRien a purger : aucun devis ni facture en base.")
        return

    if "--force" not in sys.argv:
        print(
            "\nCette operation supprime DEFINITIVEMENT tous les devis et factures "
            "(le catalogue, les clients et la societe sont conserves)."
        )
        reponse = input("Confirmer la purge ? Tapez 'oui' : ").strip().lower()
        if reponse != "oui":
            print("Annule.")
            return

    with sync_engine.begin() as conn:
        # Un seul TRUNCATE sur les deux tables racines : le CASCADE propage aux enfants.
        conn.execute(
            text(f"TRUNCATE TABLE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
        )

    with sync_engine.connect() as conn:
        apres = _compter(conn)

    print("\nPurge effectuee. Etat final :")
    for tbl, n in apres.items():
        print(f"  {tbl:<24} {n}")


if __name__ == "__main__":
    purger()
