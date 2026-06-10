"""Endpoints sur une piece jointe identifiee par son id (telechargement, edition,
mise a la corbeille). L'upload et la liste, eux, sont rattaches a un devis et
vivent dans routes/devis.py.
"""

from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.devis_document import DevisDocument, CATEGORIES_DOCUMENT

router = APIRouter()


class DocumentPatchRequest(BaseModel):
    categorie: str | None = None
    tag: str | None = None
    commentaire: str | None = None


@router.get("/{doc_id}/download")
async def telecharger_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Renvoie le contenu binaire de la piece jointe (force le telechargement)."""
    doc = await db.get(DevisDocument, doc_id)
    if not doc or doc.archived_at is not None:
        raise HTTPException(404, "Document non trouve")
    # filename* (RFC 5987) gere les accents ; filename ASCII en repli.
    nom = doc.nom_fichier or f"document-{doc.id}"
    disposition = (
        f"attachment; filename=\"{nom.encode('ascii', 'ignore').decode() or 'document'}\"; "
        f"filename*=UTF-8''{quote(nom)}"
    )
    return Response(
        content=doc.contenu,
        media_type=doc.mime_type or "application/octet-stream",
        headers={"Content-Disposition": disposition},
    )


@router.patch("/{doc_id}")
async def modifier_document(
    doc_id: int, data: DocumentPatchRequest, db: AsyncSession = Depends(get_db)
):
    """Met a jour les metadonnees editables : categorie, tag, commentaire."""
    doc = await db.get(DevisDocument, doc_id)
    if not doc or doc.archived_at is not None:
        raise HTTPException(404, "Document non trouve")
    if data.categorie is not None:
        if data.categorie not in CATEGORIES_DOCUMENT:
            raise HTTPException(400, "Categorie invalide")
        doc.categorie = data.categorie
    if data.tag is not None:
        doc.tag = data.tag.strip() or None
    if data.commentaire is not None:
        doc.commentaire = data.commentaire.strip() or None
    await db.commit()
    return {"id": doc.id, "ok": True}


@router.delete("/{doc_id}", status_code=204)
async def archiver_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Met la piece a la corbeille (soft-delete). Restaurable via /restaurer."""
    doc = await db.get(DevisDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document non trouve")
    if doc.archived_at is None:
        doc.archived_at = datetime.now(timezone.utc)
        await db.commit()
    return Response(status_code=204)


@router.post("/{doc_id}/restaurer")
async def restaurer_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Sort la piece de la corbeille (annule le soft-delete)."""
    doc = await db.get(DevisDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document non trouve")
    doc.archived_at = None
    await db.commit()
    return {"id": doc.id, "ok": True}
