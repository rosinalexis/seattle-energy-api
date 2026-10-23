"""Tests du pipeline du modèle et de sa cohérence avec le contrat de l'API."""

from typing import get_args

import pandas as pd

from app.ml.modele import ajouter_features_derivees
from app.schemas.prediction import Quartier, TypeUsage


def test_features_derivees_calcule_age_et_surface_par_etage():
    batiments = pd.DataFrame(
        {"annee_construction": [2000], "surface_batie": [1000], "nombre_etages": [4]}
    )

    resultat = ajouter_features_derivees(batiments)

    assert resultat.loc[0, "age_batiment"] == 16
    assert resultat.loc[0, "surface_par_etage"] == 250


def test_features_derivees_ne_modifie_pas_les_donnees_recues():
    batiments = pd.DataFrame(
        {"annee_construction": [2000], "surface_batie": [1000], "nombre_etages": [4]}
    )

    ajouter_features_derivees(batiments)

    assert list(batiments.columns) == ["annee_construction", "surface_batie", "nombre_etages"]


def test_categories_acceptees_par_l_api_identiques_a_celles_apprises(modele):
    # Une catégorie acceptée par l'API mais inconnue du modèle serait encodée en zéros :
    # la prédiction serait fausse sans aucune erreur visible.
    encodeur = modele.named_steps["preparation"].named_transformers_["categorielles"]
    types_appris, quartiers_appris = encodeur.categories_

    assert set(get_args(TypeUsage)) == set(types_appris)
    assert set(get_args(Quartier)) == set(quartiers_appris)
