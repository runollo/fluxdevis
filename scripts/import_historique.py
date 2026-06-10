"""Import de l'historique de facturation reel (Omnipub + ASK-VSE) dans FluxDevis.

Reconstitue dans FluxDevis les factures DEJA EMISES hors application, pour que le
systeme devienne la source unique et enchaine proprement la numerotation a
F2026-010 :

  - OMNIPUB : devis FW-RAI-25122012 (15/12/2025, plan 25/25/25/25) + sa seule
    facture reellement emise F2026-001 (acompte 25 %, emise/impayee). Les 3
    versements restants seront emis plus tard via FluxDevis (010, 011, 012).
  - ASK-VSE : devis 16 (reference corrigee FW-RAI-26032511, mise en ligne
    26/05/2026) ; ses factures de TEST sont remplacees par les vraies
    F2026-005..009 (005/006 payees, 007/008/009 emises).
  - Compteur 2026 positionne a 9 -> prochaine facture emise = F2026-010.

Idempotent : re-executable sans creer de doublons.

Usage :
    cd /home/ullop/.openclaw/workspace/projects/fluxdevis
    backend/.venv/bin/python scripts/import_historique.py
"""

import sys
import os
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import sync_engine
from app.models.devis import Devis, StatutDevis, ModeReglement, PlanPaiement
from app.models.facture import Facture, FactureLigne, TypeFacture, StatutFacture

D = Decimal


def _facture(session, numero, **kw):
    """Cree une facture + sa ligne unique si le numero n'existe pas deja."""
    existe = session.scalar(select(Facture).where(Facture.numero == numero))
    if existe:
        print(f"  = {numero} existe deja, ignore")
        return existe
    ligne = FactureLigne(
        ordre=0, designation=kw["objet"], quantite=1,
        prix_unitaire_ht=kw["total_ht"], taux_tva=D("0.20"), montant_ht=kw["total_ht"],
    )
    f = Facture(numero=numero, lignes=[ligne], **kw)
    session.add(f)
    print(f"  + {numero} ({kw['type'].value}, {kw['statut'].value}, {kw['total_ttc']} TTC)")
    return f


def importer():
    with Session(sync_engine) as session:
        # ----- OMNIPUB : devis + facture F2026-001 -----
        print("OMNIPUB")
        dev_omni = session.scalar(
            select(Devis).where(Devis.reference == "FW-RAI-25122012")
        )
        if not dev_omni:
            dev_omni = Devis(
                reference="FW-RAI-25122012",
                document_type="devis",
                statut=StatutDevis.ACCEPTE,
                date_emission=date(2025, 12, 15),
                date_validite=date(2026, 1, 15),
                client_id=3,  # OMNIPUB
                client_raison_sociale="OMNIPUB",
                client_adresse="199 rue Hélène Boucher",
                client_cp="34170",
                client_ville="Castelnau-le-Lez",
                client_interlocuteur="M. Sylvain Lombardi",
                client_email="sl@omnipub.net",
                client_siret="43276478500023",
                offre_id=2,  # Webflow (detail non disponible : a affiner si besoin)
                offre_nom="Création et mise en place du site web professionnel",
                offre_type_site="Webflow",
                offre_prix_catalogue=D("5171.68"),
                mode_reglement=ModeReglement.COMPTANT,
                plan_paiement=PlanPaiement.VINGTCINQ_X4,
                prix_vente_final=D("5171.68"),
                total_prestations_ht=D("5171.68"),
                total_ht=D("5171.68"),
                total_tva=D("1034.32"),
                total_ttc=D("6206.00"),
            )
            session.add(dev_omni)
            session.flush()
            print(f"  + devis FW-RAI-25122012 (id {dev_omni.id}, 6206.00 TTC)")
        else:
            print(f"  = devis FW-RAI-25122012 existe (id {dev_omni.id})")

        _facture(
            session, "F2026-001",
            type=TypeFacture.ACOMPTE, statut=StatutFacture.EMISE,
            devis_id=dev_omni.id,
            date_emission=date(2026, 4, 10), date_echeance=date(2026, 4, 10),
            objet="Acompte 25 % à la signature sur devis FW-RAI-25122012 — Création site web professionnel Omnipub",
            total_ht=D("1292.92"), total_tva=D("258.58"), total_ttc=D("1551.50"),
        )

        # ----- ASK-VSE : devis 16 + factures F2026-005..009 -----
        print("ASK-VSE")
        dev_ask = session.get(Devis, 16)
        if dev_ask:
            dev_ask.reference = "FW-RAI-26032511"
            dev_ask.statut = StatutDevis.ACCEPTE
            dev_ask.date_mise_en_ligne = date(2026, 5, 26)
            if not dev_ask.client_email:
                dev_ask.client_email = "contact@askvse.fr"
            print("  ~ devis 16 -> reference FW-RAI-26032511, mise en ligne 26/05/2026")
            # Suppression des factures de TEST (numeros horodates provisoires)
            tests = session.scalars(
                select(Facture).where(
                    Facture.devis_id == 16, Facture.numero.like("F-ASKV-%")
                )
            ).all()
            for f in tests:
                print(f"  - suppression facture test {f.numero}")
                session.delete(f)
            session.flush()
        else:
            print("  ! devis 16 introuvable — factures ASK-VSE NON creees")
            dev_ask = None

        if dev_ask:
            ref = "FW-RAI-26032511"
            off = "Croissance 8 pages"
            _facture(
                session, "F2026-005",
                type=TypeFacture.ACOMPTE, statut=StatutFacture.PAYEE,
                devis_id=16, date_emission=date(2026, 4, 15), date_echeance=date(2026, 4, 15),
                date_paiement=date(2026, 4, 15), moyen_paiement="Virement",
                objet=f"Premier versement – 33 % à la signature sur devis {ref}",
                total_ht=D("1003.58"), total_tva=D("200.72"), total_ttc=D("1204.30"),
            )
            _facture(
                session, "F2026-006",
                type=TypeFacture.ACOMPTE, statut=StatutFacture.PAYEE,
                devis_id=16, date_emission=date(2026, 5, 15), date_echeance=date(2026, 5, 15),
                date_paiement=date(2026, 5, 15), moyen_paiement="Virement",
                objet=f"Deuxième versement – 33 % à 30 jours sur devis {ref}",
                total_ht=D("1003.59"), total_tva=D("200.72"), total_ttc=D("1204.31"),
            )
            _facture(
                session, "F2026-007",
                type=TypeFacture.SOLDE, statut=StatutFacture.EMISE,
                devis_id=16, date_emission=date(2026, 6, 14), date_echeance=date(2026, 6, 14),
                objet=f"Troisième et dernier versement – 33 % à 60 jours sur devis {ref}",
                total_ht=D("1003.59"), total_tva=D("200.72"), total_ttc=D("1204.31"),
            )
            _facture(
                session, "F2026-008",
                type=TypeFacture.MAINTENANCE, statut=StatutFacture.EMISE,
                devis_id=16, date_emission=date(2026, 5, 26), date_echeance=date(2026, 5, 26),
                periode_debut=date(2026, 5, 26), periode_fin=date(2026, 6, 25),
                objet=f"Maintenance & hébergement — {off} — période du 26/05/2026 au 25/06/2026",
                total_ht=D("48.29"), total_tva=D("9.66"), total_ttc=D("57.95"),
            )
            _facture(
                session, "F2026-009",
                type=TypeFacture.MAINTENANCE, statut=StatutFacture.EMISE,
                devis_id=16, date_emission=date(2026, 6, 26), date_echeance=date(2026, 6, 26),
                periode_debut=date(2026, 6, 26), periode_fin=date(2026, 7, 25),
                objet=f"Maintenance & hébergement — {off} — période du 26/06/2026 au 25/07/2026",
                total_ht=D("48.29"), total_tva=D("9.66"), total_ttc=D("57.95"),
            )

        # ----- Compteur 2026 = 9 -> prochaine emise = F2026-010 -----
        session.execute(
            text(
                """
                INSERT INTO compteur_facture (annee, dernier) VALUES (2026, 9)
                ON CONFLICT (annee) DO UPDATE SET dernier = GREATEST(compteur_facture.dernier, 9)
                """
            )
        )
        print("Compteur 2026 -> 9 (prochaine facture emise = F2026-010)")

        session.commit()
        print("\nImport termine.")


if __name__ == "__main__":
    importer()
