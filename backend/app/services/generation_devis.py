"""Service de generation de devis Word.

Devis oriente CLIENT : presentation commerciale et professionnelle.
Principe (cf. pratique des agences web) :
- la creation est presentee comme UN livrable a UN prix (pas de prix par option,
  source de friction) ; le detail du perimetre est liste sans prix ;
- les avantages (articles offerts + remise) sont mis en valeur pour materialiser
  la valeur percue ;
- l'abonnement mensuel est nettement separe (engagement recurrent distinct) ;
- ancrage de prix : valeur catalogue -> avantages -> net a payer.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from io import BytesIO

from app.services.echeances import repartir_au_centime

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.word_helpers import (
    C_NAVY, C_TEXT, C_WHITE, C_AHEAD, C_PAID, C_CURR,
    HEX_NAVY, HEX_PAID,
    fmt_eur, setup_page, force_arial, tbl_no_spacing, full_tbl_borders,
    cell_bg, cell_w, row_height, p_fmt, run, cell_text, hline, spacer,
)

D = Decimal
TVA_RATE = D("0.20")
HEX_AVANTAGE = "EEF7F1"   # vert tres clair (encadre avantages)


def _q(val) -> Decimal:
    return Decimal(str(val or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Repartition des echeances selon le plan de paiement (comptant).
_PLAN_PARTS = {
    "100%": [("Solde", Fraction(1, 1))],
    "50/50": [("Acompte 50 %", Fraction(1, 2)), ("Solde 50 %", Fraction(1, 2))],
    "33/33/33": [
        ("Acompte 1/3 (a la commande)", Fraction(1, 3)),
        ("2e versement 1/3 (a mi-parcours)", Fraction(1, 3)),
        ("Solde 1/3 (a la livraison)", Fraction(1, 3)),
    ],
    "50/25/25": [
        ("Acompte 50 % (a la commande)", Fraction(1, 2)),
        ("2e versement 25 %", Fraction(1, 4)),
        ("Solde 25 % (a la livraison)", Fraction(1, 4)),
    ],
    "25/25/25/25": [
        ("Acompte 25 % (a la commande)", Fraction(1, 4)),
        ("2e versement 25 %", Fraction(1, 4)),
        ("3e versement 25 %", Fraction(1, 4)),
        ("Solde 25 % (a la livraison)", Fraction(1, 4)),
    ],
}


def repartition_echeances(plan: str | None, total_ttc) -> list[tuple[str, Decimal]]:
    """Repartit un montant TTC selon le plan de paiement (somme exacte au centime)."""
    parts = _PLAN_PARTS.get(plan or "100%", _PLAN_PARTS["100%"])
    montants = repartir_au_centime(total_ttc, [frac for _, frac in parts])
    return [(label, montants[i]) for i, (label, _) in enumerate(parts)]


# ---------------------------------------------------------------------------
# Calcul des donnees derivees (valeur catalogue, avantages, mensuel net)
# ---------------------------------------------------------------------------

def _calcul_synthese(devis) -> dict:
    """Reconstitue les montants commerciaux a partir du snapshot du devis.

    Renvoie un dict avec : prix_creation_ht, remise_setup, offerts (liste),
    offerts_setup_total, avantages_total, valeur_catalogue,
    mensuel_brut, mensuel_net, remise_pct_recurrent.
    """
    prix_creation_ht = _q(devis.total_ht)
    remise_setup = _q(devis.remise_eur_setup)

    offerts = [
        {"designation": a.designation, "valeur": _q(a.prix_vente)}
        for a in sorted(devis.articles_offerts or [], key=lambda x: x.ordre)
    ]
    offerts_total = sum((o["valeur"] for o in offerts), D("0"))
    offerts_recurrent = _q(getattr(devis, "total_offerts_recurrent_ht", 0) or 0)
    offerts_setup_total = offerts_total - offerts_recurrent
    if offerts_setup_total < 0:
        offerts_setup_total = D("0")

    # Avantages mis en avant cote creation (one-shot) : offerts setup + remise setup.
    avantages_total = offerts_setup_total + remise_setup
    valeur_catalogue = prix_creation_ht + avantages_total

    # Mensuel : brut (catalogue) puis net (apres deduction offerts recurrent et remise).
    mensuel_brut = _q(devis.total_pack_maintenance_ht) + _q(devis.total_options_recurrent_ht)
    remise_pct = _q(devis.remise_pct_recurrent) / D("100")
    mensuel_net = _q((mensuel_brut - offerts_recurrent) * (D("1") - remise_pct))
    if mensuel_net < 0:
        mensuel_net = D("0")

    return {
        "prix_creation_ht": prix_creation_ht,
        "remise_setup": remise_setup,
        "offerts": offerts,
        "offerts_setup_total": offerts_setup_total,
        "avantages_total": avantages_total,
        "valeur_catalogue": valeur_catalogue,
        "mensuel_brut": mensuel_brut,
        "mensuel_net": mensuel_net,
    }


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

def generer_devis(devis, societe) -> BytesIO:
    """Genere un devis Word oriente client et retourne un buffer BytesIO."""
    doc = Document()
    setup_page(doc)
    force_arial(doc)

    s = _calcul_synthese(devis)

    _add_header(doc, devis, societe)
    spacer(doc, 4)
    _add_emetteur_meta(doc, devis, societe)
    spacer(doc, 4)
    _add_client_objet(doc, devis)
    spacer(doc, 6)

    _add_accroche(doc, devis)
    spacer(doc, 5)

    _add_creation(doc, devis, s)
    spacer(doc, 5)

    if s["avantages_total"] > 0:
        _add_avantages(doc, s)
        spacer(doc, 5)

    if s["mensuel_net"] > 0:
        _add_abonnement(doc, devis, s)
        spacer(doc, 5)

    _add_totaux(doc, devis, s)
    spacer(doc, 6)

    if _mode_label(devis) == "Leasing":
        _add_leasing(doc, devis)
    else:
        _add_echeancier(doc, devis)
    spacer(doc, 6)

    if devis.note_commerciale:
        _add_note(doc, devis.note_commerciale)
        spacer(doc, 4)

    _add_mentions(doc, devis, societe)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _add_header(doc, devis, societe):
    tbl = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl)
    cell = tbl.rows[0].cells[0]
    cell_bg(cell, HEX_NAVY)
    row_height(tbl.rows[0], 1.2)
    marque = (societe.marque if societe and societe.marque else None) or \
             (societe.nom if societe else "FluXweb")
    cell_text(cell, f"{marque}  —  DEVIS",
              bold=True, size=13, color=C_WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)


def _add_emetteur_meta(doc, devis, societe):
    tbl = doc.add_table(rows=1, cols=2)
    tbl_no_spacing(tbl)
    left, right = tbl.rows[0].cells[0], tbl.rows[0].cells[1]
    cell_w(left, 9)
    cell_w(right, 8)

    lignes_emetteur = []
    if societe:
        lignes_emetteur = [
            (societe.nom, True),
            (societe.forme_juridique or "", False),
            (societe.adresse or "", False),
            (societe.cp_ville or "", False),
            (f"SIRET : {societe.siret}" if societe.siret else "", False),
            (f"TVA : {societe.tva_intracom}" if societe.tva_intracom else "", False),
        ]
    for text, bold in lignes_emetteur:
        if not text:
            continue
        p = left.add_paragraph()
        p_fmt(p, before=0, after=0)
        run(p, text, bold=bold, size=8, color=C_TEXT)

    meta = [
        ("Devis n°", devis.reference),
        ("Date d’émission", devis.date_emission.strftime("%d/%m/%Y")),
        ("Valable jusqu’au", devis.date_validite.strftime("%d/%m/%Y")),
        ("Mode de règlement", _mode_label(devis)),
    ]
    if devis.commercial:
        meta.append(("Commercial", devis.commercial))
    for label, val in meta:
        p = right.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_fmt(p, before=0, after=0)
        run(p, f"{label} : ", bold=True, size=8, color=C_TEXT)
        run(p, str(val), size=8, color=C_TEXT)


def _add_client_objet(doc, devis):
    tbl = doc.add_table(rows=1, cols=2)
    tbl_no_spacing(tbl)
    left, right = tbl.rows[0].cells[0], tbl.rows[0].cells[1]
    cell_w(left, 9)
    cell_w(right, 8)

    p = left.add_paragraph()
    p_fmt(p, before=0, after=1)
    run(p, "DESTINATAIRE", bold=True, size=7, color=C_NAVY)
    cp_ville = " ".join(x for x in [devis.client_cp, devis.client_ville] if x)
    for line in [
        devis.client_raison_sociale,
        devis.client_interlocuteur,
        devis.client_adresse,
        cp_ville,
        f"SIRET : {devis.client_siret}" if devis.client_siret else "",
        f"Tél : {devis.client_telephone}" if devis.client_telephone else "",
    ]:
        if line:
            p = left.add_paragraph()
            p_fmt(p, before=0, after=0)
            run(p, line, size=8, color=C_TEXT)

    p = right.add_paragraph()
    p_fmt(p, before=0, after=1)
    run(p, "OBJET", bold=True, size=7, color=C_NAVY)
    p = right.add_paragraph()
    p_fmt(p, before=0, after=0)
    objet = "Création de votre site internet"
    run(p, objet, size=8, color=C_TEXT)
    p = right.add_paragraph()
    p_fmt(p, before=0, after=0)
    sous = f"{devis.offre_nom}" + (f" ({devis.offre_type_site})" if devis.offre_type_site else "")
    run(p, sous, size=8, color=C_AHEAD)


def _add_accroche(doc, devis):
    texte = (devis.accroche or "").strip() or (
        "Voici notre proposition pour la création de votre site internet, "
        "pensé pour renforcer votre visibilité et convertir vos visiteurs en clients."
    )
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=0)
    run(p, texte, italic=True, size=9, color=C_TEXT)


def _items_offerts_designations(devis) -> set[str]:
    return {(a.designation or "").strip() for a in (devis.articles_offerts or [])}


def _add_creation(doc, devis, s):
    """Section CREATION : titre offre + perimetre (sans prix) + prix unique."""
    offerts_noms = _items_offerts_designations(devis)

    # En-tete de section (bandeau navy)
    tbl_head = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl_head)
    cell_bg(tbl_head.rows[0].cells[0], HEX_NAVY)
    cell_text(tbl_head.rows[0].cells[0], "CRÉATION DE VOTRE SITE",
              bold=True, size=10, color=C_WHITE)

    # Corps : sous-titre + liste a puces + prix
    tbl = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    cell = tbl.rows[0].cells[0]
    cell_w(cell, 17)

    # Sous-titre (l'offre)
    p = cell.paragraphs[0]
    p_fmt(p, before=2, after=2)
    titre = f"Site {devis.offre_nom}"
    if devis.offre_type_site:
        titre += f" ({devis.offre_type_site})"
    run(p, titre, bold=True, size=9, color=C_NAVY)

    # Perimetre
    p = cell.add_paragraph()
    p_fmt(p, before=2, after=1)
    run(p, "Votre projet comprend :", bold=True, size=8, color=C_TEXT)

    # Construire la liste (sans prix) : prestations + options setup (payantes + incluses)
    puces = []
    for lg in sorted(devis.lignes or [], key=lambda x: x.ordre):
        nom = (lg.designation or "").strip()
        if nom:
            puces.append((nom, "offert" if nom in offerts_noms else "normal"))
    for opt in sorted(devis.options or [], key=lambda x: x.ordre):
        type_ligne = (opt.type_ligne or "").upper()
        if type_ligne in ("RECURRENT", "OPTION_RECURRENT", "PACK"):
            continue  # va dans l'abonnement
        nom = (opt.nom or "").strip()
        if not nom:
            continue
        qte = opt.quantite or 1
        libelle = nom if qte <= 1 else f"{nom} (x{qte})"
        if nom in offerts_noms:
            etat = "offert"
        elif opt.inclus or _q(opt.prix_setup_ht) == 0:
            etat = "inclus"
        else:
            etat = "normal"
        puces.append((libelle, etat))

    for libelle, etat in puces:
        p = cell.add_paragraph()
        p_fmt(p, before=0, after=0)
        run(p, "•  ", size=8, color=C_NAVY)
        run(p, libelle, size=8, color=C_TEXT)
        if etat == "offert":
            run(p, "  (offert)", size=8, color=C_PAID, bold=True)
        elif etat == "inclus":
            run(p, "  (inclus)", size=8, color=C_AHEAD, italic=True)

    # Prix de la creation
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_fmt(p, before=4, after=2)
    run(p, "Prix de la création HT : ", bold=True, size=10, color=C_TEXT)
    run(p, fmt_eur(s["prix_creation_ht"]), bold=True, size=11, color=C_NAVY)


def _add_avantages(doc, s):
    """Encadre VOS AVANTAGES : offerts (valeur) + remise + total."""
    rows = []
    for o in s["offerts"]:
        rows.append((f"Offert : {o['designation']}", "valeur " + fmt_eur(o["valeur"])))
    if s["remise_setup"] > 0:
        rows.append(("Remise commerciale", "− " + fmt_eur(s["remise_setup"])))

    # En-tete
    tbl_head = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl_head)
    cell_bg(tbl_head.rows[0].cells[0], HEX_PAID)
    cell_text(tbl_head.rows[0].cells[0], "VOS AVANTAGES", bold=True, size=10, color=C_PAID)

    tbl = doc.add_table(rows=len(rows) + 1, cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    for i, (label, val) in enumerate(rows):
        cell_bg(tbl.rows[i].cells[0], HEX_AVANTAGE)
        cell_bg(tbl.rows[i].cells[1], HEX_AVANTAGE)
        cell_w(tbl.rows[i].cells[0], 13)
        cell_w(tbl.rows[i].cells[1], 4)
        cell_text(tbl.rows[i].cells[0], label, size=8, color=C_PAID)
        cell_text(tbl.rows[i].cells[1], val, size=8, color=C_PAID,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)

    # Total avantages (ligne mise en avant)
    last = len(rows)
    cell_bg(tbl.rows[last].cells[0], HEX_PAID)
    cell_bg(tbl.rows[last].cells[1], HEX_PAID)
    cell_w(tbl.rows[last].cells[0], 13)
    cell_w(tbl.rows[last].cells[1], 4)
    cell_text(tbl.rows[last].cells[0],
              "Soit un total d’avantages offerts sur votre projet",
              bold=True, size=8, color=C_PAID)
    cell_text(tbl.rows[last].cells[1], fmt_eur(s["avantages_total"]),
              bold=True, size=9, color=C_PAID, align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_abonnement(doc, devis, s):
    """Section ABONNEMENT MENSUEL : perimetre recurrent + mensuel HT/TTC."""
    # En-tete
    tbl_head = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl_head)
    cell_bg(tbl_head.rows[0].cells[0], HEX_NAVY)
    cell_text(tbl_head.rows[0].cells[0], "ABONNEMENT MENSUEL",
              bold=True, size=10, color=C_WHITE)

    tbl = doc.add_table(rows=1, cols=1)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    cell = tbl.rows[0].cells[0]
    cell_w(cell, 17)

    p = cell.paragraphs[0]
    p_fmt(p, before=2, after=1)
    run(p, "Comprend :", bold=True, size=8, color=C_TEXT)

    for opt in sorted(devis.options or [], key=lambda x: x.ordre):
        type_ligne = (opt.type_ligne or "").upper()
        if type_ligne not in ("RECURRENT", "OPTION_RECURRENT", "PACK"):
            continue
        nom = (opt.nom or "").strip()
        if not nom:
            continue
        p = cell.add_paragraph()
        p_fmt(p, before=0, after=0)
        run(p, "•  ", size=8, color=C_NAVY)
        run(p, nom, size=8, color=C_TEXT)
        if opt.inclus:
            run(p, "  (inclus)", size=8, color=C_AHEAD, italic=True)

    mensuel_net = s["mensuel_net"]
    mensuel_brut = s["mensuel_brut"]
    mensuel_ttc = _q(mensuel_net * (D("1") + TVA_RATE))

    # Prix mensuel (avec catalogue barre si avantage)
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_fmt(p, before=4, after=0)
    if mensuel_brut > mensuel_net:
        run(p, fmt_eur(mensuel_brut) + " ", size=9, color=C_AHEAD, strike=True)
    run(p, "Abonnement HT : ", bold=True, size=9, color=C_TEXT)
    run(p, fmt_eur(mensuel_net) + " /mois", bold=True, size=10, color=C_NAVY)

    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_fmt(p, before=0, after=2)
    run(p, "Abonnement TTC : ", bold=True, size=9, color=C_TEXT)
    run(p, fmt_eur(mensuel_ttc) + " /mois", bold=True, size=10, color=C_NAVY)

    # Note
    p = doc.add_paragraph()
    p_fmt(p, before=2, after=0)
    run(p, "Démarre à la mise en ligne du site. Sans engagement de durée.",
        italic=True, size=7, color=C_AHEAD)


def _add_totaux(doc, devis, s):
    """Bloc totaux : ancrage valeur catalogue -> avantages -> net a payer TTC."""
    lignes = []
    if s["avantages_total"] > 0:
        lignes.append(("Valeur catalogue HT", fmt_eur(s["valeur_catalogue"]), False, False))
        lignes.append(("Avantages offerts", "− " + fmt_eur(s["avantages_total"]), False, False))
    lignes.append(("Total HT", fmt_eur(_q(devis.total_ht)), False, False))
    lignes.append(("TVA 20 %", fmt_eur(_q(devis.total_tva)), False, False))
    lignes.append(("NET À PAYER (création)", fmt_eur(_q(devis.total_ttc)), True, True))

    tbl = doc.add_table(rows=len(lignes), cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    for i, (label, val, is_total, _) in enumerate(lignes):
        cell_w(tbl.rows[i].cells[0], 13)
        cell_w(tbl.rows[i].cells[1], 4)
        if is_total:
            cell_bg(tbl.rows[i].cells[0], HEX_NAVY)
            cell_bg(tbl.rows[i].cells[1], HEX_NAVY)
        color = C_WHITE if is_total else C_TEXT
        size = 10 if is_total else 9
        cell_text(tbl.rows[i].cells[0], label, bold=is_total, size=size, color=color,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)
        cell_text(tbl.rows[i].cells[1], val + (" TTC" if is_total else ""),
                  bold=is_total, size=size, color=color, align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_echeancier(doc, devis):
    parts = repartition_echeances(_plan_label(devis), devis.total_ttc)
    if len(parts) <= 1:
        return  # 100 % : pas d'echeancier a detailler

    p = doc.add_paragraph()
    run(p, "Échéancier de paiement", bold=True, size=9, color=C_NAVY)

    tbl = doc.add_table(rows=1 + len(parts), cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    for i, h in enumerate(["Échéance", "Montant TTC"]):
        cell_bg(tbl.rows[0].cells[i], HEX_NAVY)
        cell_text(tbl.rows[0].cells[i], h, bold=True, size=8, color=C_WHITE,
                  align=WD_ALIGN_PARAGRAPH.CENTER if i == 1 else WD_ALIGN_PARAGRAPH.LEFT)

    for idx, (label, montant) in enumerate(parts, start=1):
        cell_w(tbl.rows[idx].cells[0], 13)
        cell_w(tbl.rows[idx].cells[1], 4)
        cell_text(tbl.rows[idx].cells[0], label, size=8)
        cell_text(tbl.rows[idx].cells[1], fmt_eur(montant), size=8,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_leasing(doc, devis):
    p = doc.add_paragraph()
    run(p, "Financement (location évolutive)", bold=True, size=9, color=C_NAVY)

    lignes = []
    if devis.loyer_mensuel:
        lignes.append(("Loyer mensuel HT", fmt_eur(_q(devis.loyer_mensuel)) + " /mois"))
    if devis.duree_financement_mois:
        lignes.append(("Durée du financement", f"{devis.duree_financement_mois} mois"))
    if devis.montant_finance:
        lignes.append(("Montant financé", fmt_eur(_q(devis.montant_finance))))
    if not lignes:
        return

    tbl = doc.add_table(rows=len(lignes), cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    for i, (label, val) in enumerate(lignes):
        cell_w(tbl.rows[i].cells[0], 13)
        cell_w(tbl.rows[i].cells[1], 4)
        cell_text(tbl.rows[i].cells[0], label, bold=True, size=8, color=C_TEXT,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)
        cell_text(tbl.rows[i].cells[1], val, size=8, color=C_TEXT,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_note(doc, note):
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=1)
    run(p, "Note", bold=True, size=7, color=C_NAVY)
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=0)
    run(p, note, size=8, color=C_TEXT)


def _add_mentions(doc, devis, societe):
    hline(doc)
    mentions = [
        f"Devis valable jusqu’au {devis.date_validite.strftime('%d/%m/%Y')}.",
        "Pour acceptation, retourner ce devis daté et signé avec la mention "
        "« Bon pour accord ».",
    ]
    if societe and societe.iban:
        mentions.append(
            f"Règlement par virement bancaire : IBAN {societe.iban}"
            + (f" — BIC {societe.bic}" if societe.bic else "")
        )
    mentions.append("Prix exprimés en euros. TVA au taux en vigueur (20 %).")
    for m in mentions:
        p = doc.add_paragraph()
        p_fmt(p, before=0, after=1)
        run(p, m, italic=True, size=7, color=C_AHEAD)

    # Zone de signature
    spacer(doc, 8)
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=0)
    run(p, "Bon pour accord, le ......./......./...........", bold=True, size=8, color=C_TEXT)
    p = doc.add_paragraph()
    p_fmt(p, before=2, after=0)
    run(p, "Signature du client (précédée de la mention « Bon pour accord ») :",
        size=8, color=C_TEXT)


def _mode_label(devis) -> str:
    m = devis.mode_reglement
    return m.value if hasattr(m, "value") else str(m)


def _plan_label(devis) -> str:
    p = devis.plan_paiement
    if p is None:
        return "100%"
    return p.value if hasattr(p, "value") else str(p)
