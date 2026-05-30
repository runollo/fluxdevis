"""Recalcule les prix derives de toutes les options existantes en base.

A lancer apres une correction de la formule de tarification
(Option.recalculer_prix). Ne touche pas aux donnees source (heures, marge,
prix_heure, prix_hebergement) ni aux devis deja emis (prix figes).

Usage (depuis la racine du projet) :
    PYTHONPATH=backend backend/.venv/bin/python scripts/resync_prix_options.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SyncSessionLocal
from app.models.option import Option


def main():
    with SyncSessionLocal() as session:
        options = session.query(Option).all()
        modifies = 0
        for o in options:
            avant = (o.setup_achat, o.mensuel_achat, o.vente_setup, o.vente_mensuel)
            o.recalculer_prix()
            apres = (o.setup_achat, o.mensuel_achat, o.vente_setup, o.vente_mensuel)
            if avant != apres:
                modifies += 1
                print(f"{o.code:22} vente_mensuel {avant[3]} -> {apres[3]}  | vente_setup {avant[2]} -> {apres[2]}")
        session.commit()
        print(f"\n{modifies} option(s) recalculee(s) sur {len(options)}.")


if __name__ == "__main__":
    main()
