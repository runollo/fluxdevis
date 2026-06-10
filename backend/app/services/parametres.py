"""Acces aux parametres applicatifs (singleton) et resolution de la config SMTP.

La config effective fusionne la base (prioritaire) et le .env (repli) : pour chaque
champ, on prend la valeur en base si elle est renseignee, sinon celle du .env. Cela
permet de configurer l'envoi depuis l'UI tout en gardant les defauts du .env.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.parametres import Parametres


@dataclass
class SmtpConfig:
    host: str
    port: int
    starttls: bool
    user: str
    password: str
    sender: str  # expediteur affiche (From), ex 'FluXweb <contact@fluxweb.fr>'

    @property
    def actif(self) -> bool:
        """Vrai si l'envoi SMTP est exploitable (serveur + identifiants presents)."""
        return bool(self.host and self.user and self.password)


async def charger(db: AsyncSession) -> Parametres:
    """Renvoie la ligne unique de parametres (la cree si absente)."""
    p = await db.get(Parametres, 1)
    if p is None:
        p = Parametres(id=1)
        db.add(p)
        await db.commit()
        await db.refresh(p)
    return p


async def smtp_config(db: AsyncSession) -> SmtpConfig:
    """Config SMTP effective : base (prioritaire) fusionnee avec le .env (repli)."""
    s = get_settings()
    p = await db.get(Parametres, 1)

    def champ(val, defaut):
        return val if val not in (None, "") else defaut

    return SmtpConfig(
        host=champ(p.smtp_host if p else None, s.SMTP_HOST),
        port=(p.smtp_port if (p and p.smtp_port) else s.SMTP_PORT),
        starttls=(p.smtp_starttls if (p and p.smtp_starttls is not None) else s.SMTP_STARTTLS),
        user=champ(p.smtp_user if p else None, s.SMTP_USER),
        password=champ(p.smtp_password if p else None, s.SMTP_PASSWORD),
        sender=champ(p.smtp_from if p else None, s.SMTP_FROM),
    )
