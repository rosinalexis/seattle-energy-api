"""Logique de prédiction, indépendante du protocole HTTP."""

import pandas as pd
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.config import VERSION
from app.models import PredictionEntree, PredictionSortie
from app.schemas.prediction import Batiment


def predire_consommation(batiment: Batiment, modele: Pipeline) -> float:
    """Prédit la consommation annuelle d'un bâtiment, en kBtu."""
    # Le pipeline attend un tableau (une ligne par bâtiment) avec les noms de colonnes de
    # l'entraînement : les champs du schéma portent justement ces noms.
    donnees = pd.DataFrame([batiment.model_dump()])
    return float(modele.predict(donnees)[0])


def predire_et_enregistrer(
    batiment: Batiment,
    modele: Pipeline,
    session: Session,
    batiment_id: int | None = None,
) -> PredictionSortie:
    """Prédit la consommation d'un bâtiment en traçant l'entrée et la sortie en base.

    batiment_id relie la prédiction à un bâtiment du dataset, quand elle porte sur l'un d'eux.
    """
    entree = PredictionEntree(**batiment.model_dump(), batiment_id=batiment_id)
    session.add(entree)
    # Enregistrée avant l'appel au modèle : s'il échoue, la tentative reste tracée.
    session.commit()

    sortie = PredictionSortie(
        entree=entree,
        consommation_kbtu=predire_consommation(batiment, modele),
        version_modele=VERSION,
    )
    session.add(sortie)
    session.commit()
    return sortie
