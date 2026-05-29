"""Configuration de l'application FluxDevis."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FluxDevis"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Base de donnees
    DATABASE_URL: str = "postgresql+asyncpg://fluxdevis:fluxdevis@localhost:5432/fluxdevis"
    DATABASE_URL_SYNC: str = "postgresql://fluxdevis:fluxdevis@localhost:5432/fluxdevis"

    # Securite
    SECRET_KEY: str = "change-me-in-production"
    SHEET_PASSWORD: str = "fluxweb2024"
    SHEET_PASSWORD_APPORTEUR: str = "apporteur2024"

    # TVA
    TVA_RATE: float = 0.20

    # Envoi d'emails (Resend)
    # RESEND_API_KEY : cle API Resend (re_...). Vide = envoi desactive.
    # RESEND_FROM : expediteur, ex 'FluXweb <factures@mondomaine.fr>' (domaine
    #   verifie cote Resend). Vide = fallback sur la societe en base.
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = ""

    # Fichiers
    TEMPLATES_DIR: str = "app/templates"
    GENERATED_DIR: str = "generated"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
