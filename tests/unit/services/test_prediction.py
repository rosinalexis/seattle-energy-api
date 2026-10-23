"""Tests unitaires du service de prédiction, sans passer par HTTP."""

import pytest

from app.config import VERSION
from app.models import PredictionEntree
from app.schemas.prediction import Batiment
from app.services.prediction import predire_consommation, predire_et_enregistrer


def test_predire_consommation_renvoie_un_nombre_positif(batiment, modele):
    consommation = predire_consommation(Batiment(**batiment), modele)

    assert isinstance(consommation, float)
    assert consommation > 0


def test_predire_consommation_est_reproductible(batiment, modele):
    # Le même bâtiment doit toujours donner la même prédiction.
    premiere = predire_consommation(Batiment(**batiment), modele)
    seconde = predire_consommation(Batiment(**batiment), modele)

    assert premiere == seconde


def test_predire_et_enregistrer_trace_l_entree_et_la_sortie(batiment, modele, session):
    sortie = predire_et_enregistrer(Batiment(**batiment), modele, session)

    entree = session.get(PredictionEntree, sortie.entree_id)
    # L'entrée en base est exactement ce qui a été envoyé au modèle.
    assert {champ: getattr(entree, champ) for champ in batiment} == batiment
    assert sortie.consommation_kbtu == predire_consommation(Batiment(**batiment), modele)
    assert sortie.version_modele == VERSION
    assert entree.cree_le is not None


def test_l_entree_est_tracee_meme_si_le_modele_echoue(batiment, session):
    class ModeleEnPanne:
        def predict(self, donnees):
            raise RuntimeError("panne du modèle")

    nb_entrees_avant = session.query(PredictionEntree).count()

    with pytest.raises(RuntimeError):
        predire_et_enregistrer(Batiment(**batiment), ModeleEnPanne(), session)

    assert session.query(PredictionEntree).count() == nb_entrees_avant + 1
    # La tentative est en base, sans sortie.
    derniere = session.query(PredictionEntree).order_by(PredictionEntree.id.desc()).first()
    assert derniere.sortie is None
