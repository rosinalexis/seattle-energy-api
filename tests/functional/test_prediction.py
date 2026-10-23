"""Tests fonctionnels de POST /predict, à travers HTTP comme le ferait un vrai client."""

import pytest

from app.models import PredictionEntree, PredictionSortie


def test_predict_renvoie_une_consommation_positive(client, batiment, en_tetes):
    reponse = client.post("/predict", json=batiment, headers=en_tetes)

    assert reponse.status_code == 200
    assert reponse.json()["consommation_kbtu"] > 0


def test_predict_enregistre_l_entree_et_la_sortie_en_base(client, batiment, en_tetes, session):
    reponse = client.post("/predict", json=batiment, headers=en_tetes)

    # L'identifiant renvoyé au client retrouve la prédiction en base, reliée à son entrée.
    sortie = session.get(PredictionSortie, reponse.json()["id"])
    assert sortie.consommation_kbtu == reponse.json()["consommation_kbtu"]
    assert isinstance(sortie.entree, PredictionEntree)
    assert sortie.entree.quartier == batiment["quartier"]


def test_une_requete_refusee_n_est_pas_enregistree(client, batiment, en_tetes, session):
    nb_entrees_avant = session.query(PredictionEntree).count()
    batiment["quartier"] = "PARIS"

    client.post("/predict", json=batiment, headers=en_tetes)

    # Une donnée invalide n'atteint ni le modèle ni la base.
    assert session.query(PredictionEntree).count() == nb_entrees_avant


def test_predict_refuse_une_requete_sans_cle(client, batiment):
    reponse = client.post("/predict", json=batiment)

    assert reponse.status_code == 401


def test_predict_refuse_une_mauvaise_cle(client, batiment):
    reponse = client.post("/predict", json=batiment, headers={"X-API-Key": "mauvaise-cle"})

    assert reponse.status_code == 401


# Chaque cas modifie un seul champ de l'exemple valide : si la requête est refusée,
# c'est forcément à cause de ce champ.
@pytest.mark.parametrize(
    ("champ", "valeur"),
    [
        ("quartier", "PARIS"),
        ("type_usage", "Château"),
        ("annee_construction", 2020),
        ("annee_construction", 1850),
        ("annee_construction", "mille neuf cent"),
        ("nombre_batiments", 0),
        ("nombre_etages", 0),
        ("nombre_etages", 99),
        ("surface_batie", 0),
        ("surface_parking", -1),
        ("nombre_usages", 0),
        ("part_usage_principal", 1.5),
        ("part_usage_principal", 0),
    ],
)
def test_predict_refuse_une_valeur_invalide(client, batiment, en_tetes, champ, valeur):
    batiment[champ] = valeur

    reponse = client.post("/predict", json=batiment, headers=en_tetes)

    assert reponse.status_code == 422
    # Le message d'erreur désigne le champ fautif.
    assert reponse.json()["detail"][0]["loc"][-1] == champ


def test_predict_refuse_un_champ_manquant(client, batiment, en_tetes):
    del batiment["quartier"]

    reponse = client.post("/predict", json=batiment, headers=en_tetes)

    assert reponse.status_code == 422


def test_predict_refuse_un_champ_inconnu(client, batiment, en_tetes):
    batiment["couleur"] = "bleu"

    reponse = client.post("/predict", json=batiment, headers=en_tetes)

    assert reponse.status_code == 422
