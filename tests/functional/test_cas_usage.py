"""Tests fonctionnels : le modèle complet, soumis à des cas d'usage réels à travers l'API.

Au-delà de « l'API répond », on vérifie que les prédictions respectent le bon sens physique.
"""

from typing import get_args

import pytest

from app.schemas.prediction import Quartier, TypeUsage


def predire(client, en_tetes, batiment) -> float:
    reponse = client.post("/predict", json=batiment, headers=en_tetes)
    assert reponse.status_code == 200, reponse.json()
    return reponse.json()["consommation_kbtu"]


@pytest.mark.parametrize("type_usage", get_args(TypeUsage))
def test_chaque_type_d_usage_obtient_une_prediction(client, en_tetes, batiment, type_usage):
    batiment["type_usage"] = type_usage

    assert predire(client, en_tetes, batiment) > 0


@pytest.mark.parametrize("quartier", get_args(Quartier))
def test_chaque_quartier_obtient_une_prediction(client, en_tetes, batiment, quartier):
    batiment["quartier"] = quartier

    assert predire(client, en_tetes, batiment) > 0


# Valeurs exactement aux bornes du domaine : elles doivent être acceptées, pas refusées.
@pytest.mark.parametrize(
    ("champ", "valeur"),
    [
        ("annee_construction", 1900),
        ("annee_construction", 2016),
        ("nombre_batiments", 1),
        ("nombre_batiments", 50),
        ("nombre_etages", 1),
        ("nombre_etages", 76),
        ("surface_parking", 0),
        ("part_usage_principal", 1.0),
    ],
)
def test_les_valeurs_aux_bornes_sont_acceptees(client, en_tetes, batiment, champ, valeur):
    batiment[champ] = valeur

    assert predire(client, en_tetes, batiment) > 0


def test_un_batiment_plus_grand_consomme_plus(client, en_tetes, batiment):
    petit = predire(client, en_tetes, batiment)
    batiment["surface_batie"] *= 10

    assert predire(client, en_tetes, batiment) > petit


def test_a_surface_egale_un_hopital_consomme_plus_qu_un_garde_meubles(client, en_tetes, batiment):
    # Écart mesuré dans le projet 3 : 238 kBtu/sf pour un hôpital, 15 pour un garde-meubles.
    batiment["type_usage"] = "Self-Storage Facility"
    garde_meubles = predire(client, en_tetes, batiment)
    batiment["type_usage"] = "Hospital"

    assert predire(client, en_tetes, batiment) > garde_meubles
