"""Point d'entrée de l'API : crée l'application et branche les routes.

Lancement en local : uv run uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import VERSION, get_settings
from app.database import get_engine
from app.ml.modele import charger_modele
from app.routers import prediction


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Vérifiés au démarrage : si la configuration, le modèle ou la base manque, l'API refuse
    # de démarrer au lieu de répondre une erreur 500 à la première requête.
    get_settings()
    charger_modele()
    with get_engine().connect():
        pass
    yield


app = FastAPI(
    title="Seattle Energy API",
    description=(
        "Prédit la consommation d'énergie annuelle des bâtiments non résidentiels de Seattle "
        "à partir de caractéristiques connues sans relevé.\n\n"
        "**Authentification** : envoyer la clé d'API dans l'en-tête `X-API-Key`."
    ),
    version=VERSION,
    # Description de chaque groupe d'endpoints, affichée dans Swagger.
    openapi_tags=[
        {
            "name": "Prédiction",
            "description": "Consommation prédite par le modèle. Chaque appel est tracé en base.",
        },
        {"name": "Supervision", "description": "État de l'API, sans authentification."},
    ],
    lifespan=lifespan,
)
app.include_router(prediction.router)


@app.get("/health", tags=["Supervision"], summary="Vérifier que l'API répond")
def sante() -> dict[str, str]:
    """Sans authentification : sert aux sondes de supervision (Docker, load balancer)."""
    return {"statut": "ok"}
