"""Logique de prédiction, indépendante du protocole HTTP."""

import pandas as pd
from sklearn.pipeline import Pipeline

from app.schemas.prediction import Batiment


def predire_consommation(batiment: Batiment, modele: Pipeline) -> float:
    """Prédit la consommation annuelle d'un bâtiment, en kBtu."""
    # Le pipeline attend un tableau (une ligne par bâtiment) avec les noms de colonnes de
    # l'entraînement : les champs du schéma portent justement ces noms.
    donnees = pd.DataFrame([batiment.model_dump()])
    return float(modele.predict(donnees)[0])
