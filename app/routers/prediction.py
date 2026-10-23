"""Endpoint de prédiction : traduit la requête HTTP en appel au service."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sklearn.pipeline import Pipeline

from app.ml.modele import charger_modele
from app.schemas.prediction import Batiment, Prediction
from app.securite import verifier_cle_api
from app.services.prediction import predire_consommation

router = APIRouter(tags=["Prédiction"], dependencies=[Depends(verifier_cle_api)])


@router.post(
    "/predict",
    summary="Prédire la consommation d'énergie d'un bâtiment",
    responses={
        401: {"description": "Clé d'API absente ou invalide."},
        422: {"description": "Données du bâtiment invalides ou hors du domaine du modèle."},
    },
)
def predire(
    batiment: Batiment,
    # Le modèle est injecté plutôt qu'importé : les tests peuvent le remplacer.
    modele: Annotated[Pipeline, Depends(charger_modele)],
) -> Prediction:
    """Prédit la consommation annuelle (kBtu) à partir de caractéristiques connues sans relevé."""
    return Prediction(consommation_kbtu=predire_consommation(batiment, modele))
