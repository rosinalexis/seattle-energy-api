"""Endpoint de prédiction : traduit la requête HTTP en appel au service."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.database import get_session
from app.ml.modele import charger_modele
from app.schemas.prediction import Batiment, Prediction
from app.securite import verifier_cle_api
from app.services.prediction import predire_et_enregistrer

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
    # Le modèle et la session sont injectés plutôt que créés ici : les tests peuvent les remplacer.
    modele: Annotated[Pipeline, Depends(charger_modele)],
    session: Annotated[Session, Depends(get_session)],
) -> Prediction:
    """Prédit la consommation annuelle (kBtu) à partir de caractéristiques connues sans relevé.

    L'entrée et la prédiction sont enregistrées en base ; l'identifiant renvoyé permet de les
    retrouver.
    """
    sortie = predire_et_enregistrer(batiment, modele, session)
    return Prediction(id=sortie.id, consommation_kbtu=sortie.consommation_kbtu)
