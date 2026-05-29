"""Service de generation de devis Word.

Construit un document professionnel a partir d'un Devis (snapshot fige)
et de la Societe emettrice. Reutilise les helpers Word mutualises.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from io import BytesIO

from app.services.echeances import repartir_au_centime

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.word_helpers import (
    C_NAVY, C_TEXT, C_WHITE, C_AHEAD, C_PAID,
    HEX_NAVY, HEX_PAID, HEX_CURR,
    fmt_eur, setup_page, force_arial, tbl_no_spacing, full_tbl_borders,
    cell_bg, cell_w, row_height, p_fmt, run, cell_text, hline, spacer,
)

D = Decimal
TVA_RATE = D("0.20")


def _q(val) -> Decimal:
    return Decimal(str(val or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Repartition des echeances selon le plan de paiement (comptant).
# Chaque echeance est definie par une fraction EXACTE (pas un pourcentage
# flottant) pour que 33/33/33 corresponde a des tiers reels.
_PLAN_PARTS = {
    "100%": [("Solde", Fraction(1, 1))],
    "50/50": [("Acompte 50 %", Fraction(1, 2)), ("Solde 50 %", Fraction(1, 2))],
    "33/33/33": [
        ("Acompte 1/3", Fraction(1, 3)),
        ("2e versement 1/3", Fraction(1, 3)),
        ("Solde 1/3", Fraction(1, 3)),
    ],
    "50/25/25": [
        ("Acompte 50 %", Fraction(1, 2)),
        ("2e versement 25 %", Fraction(1, 4)),
        ("Solde 25 %", Fraction(1, 4)),
    ],
    "25/25/25/25": [
        ("Acompte 25 %", Fraction(1, 4)),
        ("2e versement 25 %", Fraction(1, 4)),
        ("3e versement 25 %", Fraction(1, 4)),
        ("Solde 25 %", Fraction(1, 4)),
    ],
}


def repartition_echeances(plan: str | None, total_ttc) -> list[tuple[str, Decimal]]:
    """Repartit un montant TTC selon le plan de paiement.

    Retourne une liste de tuples (libelle, montant_ttc). La somme des montants
    vaut exactement le total : l'ecart d'arrondi est porte par le premier
    versement (cf. repartir_au_centime).
    """
    parts = _PLAN_PARTS.get(plan or "100%", _PLAN_PARTS["100%"])
    montants = repartir_au_centime(total_ttc, [frac for _, frac in parts])
    return [(label, montants[i]) for i, (label, _) in enumerate(parts)]


def generer_devis(devis, societe) -> BytesIO:
    """Genere un devis Word et retourne un buffer BytesIO.

    `devis` : instance Devis avec relations options/lignes/articles_offerts chargees.
    `societe` : instance Societe emettrice (peut etre None).
    """
    doc = Document()
    setup_page(doc)
    force_arial(doc)

    _add_header(doc, devis, societe)
    spacer(doc, 4)
    _add_emetteur_meta(doc, devis, societe)
    spacer(doc, 4)
    _add_client_objet(doc, devis)
    spacer(doc, 6)

    if devis.accroche:
        _add_accroche(doc, devis.accroche)
        spacer(doc, 4)

    _add_prestations(doc, devis)
    spacer(doc, 4)

    mensuel_brut = _q(devis.total_pack_maintenance_ht) + _q(devis.total_options_recurrent_ht)
    mensuel_ht = mensuel_brut - _q(devis.total_offerts_recurrent_ht or 0)
    if mensuel_ht < 0:
        mensuel_ht = _q(0)
    if mensuel_ht > 0:
        _add_maintenance(doc, mensuel_ht)
        spacer(doc, 4)

    articles = [a for a in devis.articles_offerts] if devis.articles_offerts else []
    if articles:
        _add_articles_offerts(doc, articles)
        spacer(doc, 4)

    _add_totaux(doc, devis)
    spacer(doc, 6)

    if str(devis.mode_reglement.value if hasattr(devis.mode_reglement, "value") else devis.mode_reglement) == "Leasing":
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
    objet = f"{devis.offre_nom}" + (f" ({devis.offre_type_site})" if devis.offre_type_site else "")
    run(p, objet, size=8, color=C_TEXT)


def _add_accroche(doc, accroche):
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=0)
    run(p, accroche, italic=True, size=9, color=C_TEXT)


def _add_prestations(doc, devis):
    """Tableau des prestations setup (one-time) : offre + lignes + options payantes."""
    rows = []

    # Offre principale
    base = f"{devis.offre_nom}"
    if devis.offre_type_site:
        base += f" ({devis.offre_type_site})"
    rows.append((base, "1", _q(devis.prix_vente_final), _q(devis.prix_vente_final)))

    # Prestations sur mesure
    for lg in sorted(devis.lignes or [], key=lambda x: x.ordre):
        qte = lg.quantite or 1
        pu = _q(lg.prix_unitaire_vente)
        rows.append((lg.designation, str(qte), pu, _q(pu * qte)))

    # Options : setup payantes + incluses
    incluses = []
    for opt in sorted(devis.options or [], key=lambda x: x.ordre):
        type_ligne = (opt.type_ligne or "").upper()
        if type_ligne in ("RECURRENT", "PACK"):
            continue  # traitees dans la section maintenance
        if opt.inclus or _q(opt.prix_setup_ht) == 0:
            incluses.append(opt.nom)
            continue
        qte = opt.quantite or 1
        pu = _q(opt.prix_setup_ht)
        rows.append((opt.nom, str(qte), pu, _q(pu * qte)))

    # En-tete de section
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=2)
    run(p, "Prestations", bold=True, size=9, color=C_NAVY)

    tbl = doc.add_table(rows=1 + len(rows), cols=4)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)

    headers = ["Désignation", "Qté", "P.U. HT", "Montant HT"]
    widths = [10.0, 1.6, 2.7, 2.7]
    for i, (h, w) in enumerate(zip(headers, widths)):
        cell_bg(tbl.rows[0].cells[i], HEX_NAVY)
        cell_w(tbl.rows[0].cells[i], w)
        cell_text(tbl.rows[0].cells[i], h, bold=True, size=8, color=C_WHITE,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

    aligns = [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER,
              WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT]
    for r_idx, (desig, qte, pu, montant) in enumerate(rows, start=1):
        vals = [desig, qte, fmt_eur(pu), fmt_eur(montant)]
        for i, (v, a, w) in enumerate(zip(vals, aligns, widths)):
            cell_w(tbl.rows[r_idx].cells[i], w)
            cell_text(tbl.rows[r_idx].cells[i], v, size=8, align=a)

    # Options incluses (listees en gris)
    if incluses:
        p = doc.add_paragraph()
        p_fmt(p, before=3, after=0)
        run(p, "Inclus dans l’offre : " + ", ".join(incluses),
            italic=True, size=7, color=C_AHEAD)


def _add_maintenance(doc, mensuel_ht):
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=2)
    run(p, "Maintenance / Abonnement mensuel", bold=True, size=9, color=C_NAVY)

    tbl = doc.add_table(rows=2, cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    cell_bg(tbl.rows[0].cells[0], HEX_NAVY)
    cell_bg(tbl.rows[0].cells[1], HEX_NAVY)
    cell_w(tbl.rows[0].cells[0], 14)
    cell_w(tbl.rows[0].cells[1], 3)
    cell_text(tbl.rows[0].cells[0], "Prestation récurrente", bold=True, size=8, color=C_WHITE)
    cell_text(tbl.rows[0].cells[1], "Mensuel HT", bold=True, size=8, color=C_WHITE,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_text(tbl.rows[1].cells[0], "Abonnement maintenance et services récurrents", size=8)
    cell_text(tbl.rows[1].cells[1], fmt_eur(mensuel_ht) + " /mois", size=8,
              align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_articles_offerts(doc, articles):
    p = doc.add_paragraph()
    p_fmt(p, before=0, after=2)
    run(p, "Articles offerts", bold=True, size=9, color=C_NAVY)

    tbl = doc.add_table(rows=1 + len(articles), cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)
    cell_bg(tbl.rows[0].cells[0], HEX_PAID)
    cell_bg(tbl.rows[0].cells[1], HEX_PAID)
    cell_w(tbl.rows[0].cells[0], 14)
    cell_w(tbl.rows[0].cells[1], 3)
    cell_text(tbl.rows[0].cells[0], "Désignation", bold=True, size=8, color=C_PAID)
    cell_text(tbl.rows[0].cells[1], "Valeur", bold=True, size=8, color=C_PAID,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    for i, art in enumerate(sorted(articles, key=lambda x: x.ordre), start=1):
        cell_text(tbl.rows[i].cells[0], art.designation, size=8, color=C_PAID)
        cell_text(tbl.rows[i].cells[1],
                  fmt_eur(_q(art.prix_vente)) + " — Offert", size=8, color=C_PAID,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)


def _add_totaux(doc, devis):
    tbl = doc.add_table(rows=4, cols=2)
    tbl_no_spacing(tbl)
    full_tbl_borders(tbl)

    lines = [
        ("Total HT", fmt_eur(_q(devis.total_ht))),
        ("TVA 20 %", fmt_eur(_q(devis.total_tva))),
        ("Total TTC", fmt_eur(_q(devis.total_ttc))),
        ("Net à payer", fmt_eur(_q(devis.total_ttc))),
    ]
    for i, (label, val) in enumerate(lines):
        cell_w(tbl.rows[i].cells[0], 14)
        cell_w(tbl.rows[i].cells[1], 3)
        is_last = i == 3
        if is_last:
            cell_bg(tbl.rows[i].cells[0], HEX_NAVY)
            cell_bg(tbl.rows[i].cells[1], HEX_NAVY)
        color = C_WHITE if is_last else C_TEXT
        cell_text(tbl.rows[i].cells[0], label, bold=True, size=9, color=color,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)
        cell_text(tbl.rows[i].cells[1], val, bold=is_last, size=9, color=color,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)


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
        cell_w(tbl.rows[idx].cells[0], 14)
        cell_w(tbl.rows[idx].cells[1], 3)
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
        cell_w(tbl.rows[i].cells[0], 14)
        cell_w(tbl.rows[i].cells[1], 3)
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
