"""Le modèle : features dérivées, préparation des colonnes et random forest, en un seul pipeline.

Le pipeline complet est sauvegardé : l'API lui donne les champs métier bruts et il applique
lui-même toutes les transformations de l'entraînement. Aucun risque d'écart entre les deux.
"""

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from app.config import ANNEE_RELEVE, MODEL_FILE, RANDOM_STATE

# L'ordre des colonnes reprend celui du projet 3 : le random forest tire des features au
# hasard par leur position, un autre ordre donnerait un autre modèle que celui évalué.
COLONNES_CATEGORIELLES = ["type_usage", "quartier"]
COLONNES_NUMERIQUES = [
    "nombre_batiments",
    "nombre_etages",
    "surface_parking",
    "surface_batie",
    "age_batiment",
    "surface_par_etage",
    "nombre_usages",
    "part_usage_principal",
]
COLONNES_BINAIRES = ["utilise_gaz", "utilise_vapeur"]

# Meilleure combinaison de la GridSearch du projet 3 (180 combinaisons, critère R²).
HYPERPARAMETRES = {
    "n_estimators": 200,
    "max_depth": None,
    "min_samples_leaf": 1,
    "max_features": 0.5,
}

# 20 % des bâtiments mis de côté pour l'évaluation finale, comme dans le projet 3.
PART_TEST = 0.2


def ajouter_features_derivees(batiments: pd.DataFrame) -> pd.DataFrame:
    """Calcule les features que le client n'a pas à fournir : l'âge et la surface par étage."""
    batiments = batiments.copy()
    batiments["age_batiment"] = ANNEE_RELEVE - batiments["annee_construction"]
    # Distingue un bâtiment étalé (entrepôt) d'une tour.
    batiments["surface_par_etage"] = batiments["surface_batie"] / batiments["nombre_etages"]
    return batiments


def construire_pipeline() -> Pipeline:
    """Assemble les étapes, de la donnée métier brute à la prédiction."""
    preparation = ColumnTransformer(
        transformers=[
            # handle_unknown="ignore" : une catégorie jamais vue donne une ligne de 0 au lieu
            # d'une erreur. L'API refuse déjà les catégories inconnues, c'est un filet de sécurité.
            (
                "categorielles",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                COLONNES_CATEGORIELLES,
            ),
            ("numeriques", StandardScaler(), COLONNES_NUMERIQUES),
            # Déjà à 0 ou 1 : rien à transformer.
            ("binaires", "passthrough", COLONNES_BINAIRES),
        ],
        # L'année de construction est remplacée par l'âge : elle ne doit pas entrer deux fois.
        remainder="drop",
    )
    return Pipeline(
        [
            ("features_derivees", FunctionTransformer(ajouter_features_derivees)),
            ("preparation", preparation),
            ("random_forest", RandomForestRegressor(random_state=RANDOM_STATE, **HYPERPARAMETRES)),
        ]
    )


def erreur_relative_mediane(y_vrai: pd.Series, y_predit: np.ndarray) -> float:
    """Erreur relative du bâtiment « typique » : médiane de |prédiction - réalité| / réalité."""
    return float(np.median(np.abs(y_predit - y_vrai) / y_vrai))


def entrainer_et_evaluer(X: pd.DataFrame, y: pd.Series) -> tuple[Pipeline, dict]:
    """Entraîne sur 80 % des bâtiments et mesure les scores sur les 20 % jamais vus."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=PART_TEST, random_state=RANDOM_STATE
    )
    pipeline = construire_pipeline().fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    metriques = {
        "batiments_entrainement": len(X_train),
        "batiments_test": len(X_test),
        "r2": round(r2_score(y_test, predictions), 3),
        "mae_kbtu": round(mean_absolute_error(y_test, predictions)),
        "rmse_kbtu": round(root_mean_squared_error(y_test, predictions)),
        "erreur_relative_mediane": round(erreur_relative_mediane(y_test, predictions), 3),
    }
    return pipeline, metriques


@lru_cache
def charger_modele() -> Pipeline:
    """Charge le modèle une seule fois : les appels suivants réutilisent le même objet."""
    return joblib.load(MODEL_FILE)
