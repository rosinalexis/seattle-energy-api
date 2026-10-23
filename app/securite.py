"""Authentification par clé d'API."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

# Déclarer l'en-tête via APIKeyHeader l'affiche dans Swagger (bouton « Authorize »).
# auto_error=False : c'est notre code qui répond, avec un message en français.
en_tete_cle_api = APIKeyHeader(name="X-API-Key", auto_error=False)


def verifier_cle_api(
    cle: Annotated[str | None, Security(en_tete_cle_api)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    # compare_digest met le même temps quelle que soit la position de la première différence :
    # un attaquant ne peut pas deviner la clé caractère par caractère en mesurant les temps
    # de réponse (attaque temporelle), ce qu'un simple == permettrait.
    if cle is None or not secrets.compare_digest(cle.encode(), settings.api_key.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé d'API absente ou invalide.",
        )
