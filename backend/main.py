"""Point d'entree de l'application FluxDevis."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import offres, options, clients, devis, factures

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API
app.include_router(offres.router, prefix="/api/offres", tags=["Offres"])
app.include_router(options.router, prefix="/api/options", tags=["Options"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(devis.router, prefix="/api/devis", tags=["Devis"])
app.include_router(factures.router, prefix="/api/factures", tags=["Factures"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
