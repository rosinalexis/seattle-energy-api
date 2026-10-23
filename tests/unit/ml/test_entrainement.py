"""Tests de l'entraînement : performances minimales et reproductibilité du modèle."""

import numpy as np
import pandas as pd
import pytest

from app.config import RAW_DATA_FILE
from app.ml.donnees import preparer_donnees
from app.ml.modele import entrainer_et_evaluer, erreur_relative_mediane

# Performances minimales acceptées : celles du modèle retenu dans le projet 3 sur son jeu de test
# (R² 0,711, erreur relative médiane 39,8 %), arrondies. Un modèle moins bon ne doit pas partir
# en production.
R2_MINIMUM = 0.70
ERREUR_RELATIVE_MAXIMUM = 0.40


@pytest.fixture(scope="module")
def entrainement():
    """Entraîne le modèle une seule fois pour tous les tests du module (≈ 15 secondes)."""
    X, y = preparer_donnees(pd.read_csv(RAW_DATA_FILE))
    pipeline, metriques = entrainer_et_evaluer(X, y)
    return X, pipeline, metriques


def test_le_jeu_de_test_contient_20_pourcent_des_batiments(entrainement):
    _, _, metriques = entrainement

    assert metriques["batiments_entrainement"] == 1265
    assert metriques["batiments_test"] == 317


def test_le_modele_atteint_les_performances_du_projet_3(entrainement):
    _, _, metriques = entrainement

    assert metriques["r2"] >= R2_MINIMUM
    assert metriques["erreur_relative_mediane"] <= ERREUR_RELATIVE_MAXIMUM


def test_l_entrainement_est_reproductible(entrainement, modele):
    # Le modèle réentraîné ici et celui sauvegardé par scripts/train_model.py doivent donner
    # exactement les mêmes prédictions : même code, mêmes données, même graine aléatoire.
    X, pipeline, _ = entrainement

    np.testing.assert_array_equal(pipeline.predict(X), modele.predict(X))


def test_erreur_relative_mediane():
    reel = pd.Series([100.0, 200.0, 400.0])
    predit = np.array([110.0, 100.0, 400.0])

    # Erreurs relatives : 10 %, 50 %, 0 % → médiane 10 %.
    assert erreur_relative_mediane(reel, predit) == pytest.approx(0.1)
