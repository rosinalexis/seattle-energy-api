"""Tests unitaires du service de prédiction, sans passer par HTTP."""

from app.schemas.prediction import Batiment
from app.services.prediction import predire_consommation


def test_predire_consommation_renvoie_un_nombre_positif(batiment, modele):
    consommation = predire_consommation(Batiment(**batiment), modele)

    assert isinstance(consommation, float)
    assert consommation > 0


def test_predire_consommation_est_reproductible(batiment, modele):
    # Le même bâtiment doit toujours donner la même prédiction.
    premiere = predire_consommation(Batiment(**batiment), modele)
    seconde = predire_consommation(Batiment(**batiment), modele)

    assert premiere == seconde
