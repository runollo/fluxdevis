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

    # Envoi d'emails — deux moteurs possibles. Le SMTP (ta propre messagerie pro)
    # est prioritaire ; Resend reste dispo en repli si jamais configure.
    #
    # SMTP (recommande : envoi depuis ta boite contact@fluxweb.fr).
    # Defauts OVH ; adapte SMTP_HOST/PORT si autre hebergeur.
    #   SMTP_USER / SMTP_PASSWORD : adresse + mot de passe de la boite (vides = envoi
    #     SMTP desactive). Pour Gmail/Microsoft, un "mot de passe d'application".
    #   SMTP_FROM : expediteur affiche, ex 'FluXweb <contact@fluxweb.fr>'. Vide =
    #     construit depuis la societe. Doit correspondre a SMTP_USER (OVH l'exige).
    SMTP_HOST: str = "ssl0.ovh.net"
    SMTP_PORT: int = 587
    SMTP_STARTTLS: bool = True  # 587 = STARTTLS ; mettre False + port 465 pour SSL direct
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Resend (alternative transactionnelle, optionnelle).
    # RESEND_API_KEY : cle API Resend (re_...). Vide = moteur Resend desactive.
    # RESEND_FROM : expediteur (domaine verifie cote Resend).
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = ""

    # Fichiers
    TEMPLATES_DIR: str = "app/templates"
    GENERATED_DIR: str = "generated"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
