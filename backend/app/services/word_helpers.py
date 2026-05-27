"""Helpers partages pour la generation de documents Word.

Extrait des fonctions dupliquees dans build_factures_acompte.py
et build_factures_maintenance.py du tarificateur.
"""

from decimal import Decimal
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# Palette navy (identique au tarificateur)
C_NAVY = RGBColor(0x1A, 0x35, 0x5E)
C_BAND = RGBColor(0x2E, 0x5F, 0x9E)
C_TEXT = RGBColor(0x1A, 0x1A, 0x1A)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_ROW_A = RGBColor(0xF5, 0xF7, 0xFA)
C_SUBTOT = RGBColor(0xE8, 0xEC, 0xF2)
C_PAID = RGBColor(0x21, 0x7A, 0x3C)
C_CURR = RGBColor(0xC0, 0x60, 0x00)
C_AHEAD = RGBColor(0x70, 0x70, 0x70)

HEX_NAVY = "1A355E"
HEX_CURR = "FFF8EC"
HEX_PAID = "EEF7F1"
HEX_BORDER = "BDC7D6"

FONT_NAME = "Arial"
NNBSP = "\u202f"
EURO = "\u20ac"


def dxa(cm: float) -> str:
    return str(int(cm * 567))


def fmt_eur(v) -> str:
    """Formate un montant en euros : 1 234,56 EUR."""
    val = float(v)
    parts = f"{val:,.2f}".replace(",", NNBSP).replace(".", ",")
    return f"{parts}{NNBSP}{EURO}"


def setup_page(doc: Document):
    """Configure la page A4 avec marges standard."""
    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)


def force_arial(doc: Document):
    """Force la police Arial sur tous les styles."""
    for style in doc.styles:
        try:
            rpr = style.element.get_or_add_rPr()
            for tag in (qn("w:rFonts"),):
                old = rpr.find(tag)
                if old is not None:
                    rpr.remove(old)
            fonts = parse_xml(
                f'<w:rFonts {nsdecls("w")} '
                f'w:ascii="{FONT_NAME}" w:hAnsi="{FONT_NAME}" '
                f'w:cs="{FONT_NAME}" w:eastAsia="{FONT_NAME}"/>'
            )
            rpr.append(fonts)
        except Exception:
            pass


def tbl_no_spacing(tbl):
    """Supprime l'espacement entre cellules."""
    props = tbl._tbl.tblPr
    if props is None:
        props = parse_xml(f"<w:tblPr {nsdecls('w')}/>")
        tbl._tbl.insert(0, props)
    spacing = parse_xml(f'<w:tblCellSpacing {nsdecls("w")} w:w="0" w:type="dxa"/>')
    props.append(spacing)


def full_tbl_borders(tbl, color: str = HEX_BORDER, sz: int = 4):
    """Applique des bordures completes a une table."""
    borders_xml = f"""<w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        <w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
    </w:tblBorders>"""
    tbl._tbl.tblPr.append(parse_xml(borders_xml))


def cell_bg(cell, hex_color: str):
    """Definit la couleur de fond d'une cellule."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def cell_w(cell, cm: float):
    """Definit la largeur d'une cellule."""
    width = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{dxa(cm)}" w:type="dxa"/>')
    cell._tc.get_or_add_tcPr().append(width)


def row_height(row, cm: float, exact: bool = True):
    """Definit la hauteur d'une ligne."""
    rule = "exact" if exact else "atLeast"
    rpr = parse_xml(f'<w:trPr {nsdecls("w")}><w:trHeight w:val="{dxa(cm)}" w:hRule="{rule}"/></w:trPr>')
    row._tr.insert(0, rpr)


def p_fmt(para, before: float = 0, after: float = 0, line: float | None = None):
    """Configure l'espacement d'un paragraphe (en points)."""
    fmt = para.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    if line is not None:
        fmt.line_spacing = Pt(line)


def run(para, text: str, bold: bool = False, size: float = 9,
        color: RGBColor | None = None, italic: bool = False, strike: bool = False):
    """Ajoute un run formate a un paragraphe."""
    r = para.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.name = FONT_NAME
    if color:
        r.font.color.rgb = color
    if italic:
        r.italic = True
    if strike:
        r.font.strike = True
    return r


def cell_text(cell, text: str, bold: bool = False, size: float = 9,
              color: RGBColor | None = None, align=WD_ALIGN_PARAGRAPH.LEFT,
              italic: bool = False, strike: bool = False,
              v_align=WD_ALIGN_VERTICAL.CENTER, before: float = 1, after: float = 1):
    """Ecrit du texte formate dans une cellule de tableau."""
    cell.vertical_alignment = v_align
    para = cell.paragraphs[0]
    para.alignment = align
    p_fmt(para, before=before, after=after)
    run(para, text, bold=bold, size=size, color=color, italic=italic, strike=strike)


def hline(doc: Document, color: str = HEX_NAVY, thickness: int = 6):
    """Ajoute une ligne horizontale."""
    para = doc.add_paragraph()
    p_fmt(para, before=2, after=2)
    pPr = para._p.get_or_add_pPr()
    borders = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:bottom w:val="single" w:sz="{thickness}" w:space="1" w:color="{color}"/>'
        f"</w:pBdr>"
    )
    pPr.append(borders)


def spacer(doc: Document, pt: float = 6):
    """Ajoute un espace vertical."""
    para = doc.add_paragraph()
    p_fmt(para, before=0, after=0, line=pt)
