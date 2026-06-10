"""Conversion de documents Word (.docx) en PDF via LibreOffice headless.

LibreOffice est le seul moteur qui rend fidelement un .docx ; on l'appelle en
ligne de commande (`soffice --headless --convert-to pdf`), sans interface. La
generation metier reste en python-docx ; on n'ajoute qu'une etape de conversion.

Le binaire (soffice/libreoffice) doit etre installe sur le serveur :
    sudo apt install --no-install-recommends libreoffice-core libreoffice-writer
"""

import asyncio
import os
import shutil
import tempfile


class PdfError(Exception):
    """Echec de conversion PDF (LibreOffice absent, delai, erreur de rendu)."""


def libreoffice_dispo() -> bool:
    return _soffice_bin() is not None


def _soffice_bin() -> str | None:
    for name in ("soffice", "libreoffice"):
        chemin = shutil.which(name)
        if chemin:
            return chemin
    return None


async def docx_vers_pdf(docx: bytes) -> bytes:
    """Convertit un .docx (bytes) en PDF (bytes). Leve PdfError en cas d'echec.

    Chaque appel utilise un profil LibreOffice dedie (UserInstallation) dans un
    dossier temporaire, pour eviter tout conflit de verrou entre conversions
    concurrentes. Le sous-processus bloquant tourne hors de la boucle asyncio.
    """
    binp = _soffice_bin()
    if not binp:
        raise PdfError(
            "LibreOffice introuvable : installez-le (sudo apt install "
            "--no-install-recommends libreoffice-core libreoffice-writer)."
        )

    tmp = tempfile.mkdtemp(prefix="fxpdf_")
    try:
        src = os.path.join(tmp, "document.docx")
        with open(src, "wb") as f:
            f.write(docx)
        profil = os.path.join(tmp, "profil")

        proc = await asyncio.create_subprocess_exec(
            binp, "--headless", "--norestore",
            f"-env:UserInstallation=file://{profil}",
            "--convert-to", "pdf", "--outdir", tmp, src,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, err = await asyncio.wait_for(proc.communicate(), timeout=90)
        except asyncio.TimeoutError:
            proc.kill()
            raise PdfError("Conversion PDF : delai depasse (LibreOffice).")

        out_pdf = os.path.join(tmp, "document.pdf")
        if proc.returncode != 0 or not os.path.exists(out_pdf):
            detail = (err.decode(errors="ignore") or "").strip()[:300]
            raise PdfError(f"Echec de la conversion PDF. {detail}")
        with open(out_pdf, "rb") as f:
            return f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
