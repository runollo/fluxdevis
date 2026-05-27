"""Routes CRUD pour les clients."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from pydantic import BaseModel

router = APIRouter()


class ClientRead(BaseModel):
    id: int
    raison_sociale: str
    adresse: str | None
    code_postal: str | None
    ville: str | None
    interlocuteur: str | None
    telephone: str | None
    email: str | None
    siret: str | None
    actif: bool

    model_config = {"from_attributes": True}


class ClientCreate(BaseModel):
    raison_sociale: str
    adresse: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    interlocuteur: str | None = None
    telephone: str | None = None
    email: str | None = None
    siret: str | None = None


class ClientUpdate(BaseModel):
    raison_sociale: str | None = None
    adresse: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    interlocuteur: str | None = None
    telephone: str | None = None
    email: str | None = None
    siret: str | None = None
    actif: bool | None = None


@router.get("/", response_model=list[ClientRead])
async def list_clients(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Client).where(Client.actif).order_by(Client.raison_sociale)
    if q:
        query = query.where(Client.raison_sociale.ilike(f"%{q}%"))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client non trouve")
    return client


@router.post("/", response_model=ClientRead, status_code=201)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db)):
    client = Client(**data.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(client_id: int, data: ClientUpdate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client non trouve")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client
