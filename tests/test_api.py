"""Tests des endpoints, à travers HTTP comme le ferait un vrai client."""

import pytest

from tests.conftest import CLE_TEST

EN_TETES = {"X-API-Key": CLE_TEST}


def test_health_repond_sans_authentification(client):
    reponse = client.get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_predict_renvoie_une_consommation_positive(client, batiment):
    reponse = client.post("/predict", json=batiment, headers=EN_TETES)

    assert reponse.status_code == 200
    assert reponse.json()["consommation_kbtu"] > 0


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
def test_predict_refuse_une_valeur_invalide(client, batiment, champ, valeur):
    batiment[champ] = valeur

    reponse = client.post("/predict", json=batiment, headers=EN_TETES)

    assert reponse.status_code == 422
    # Le message d'erreur désigne le champ fautif.
    assert reponse.json()["detail"][0]["loc"][-1] == champ


def test_predict_refuse_un_champ_manquant(client, batiment):
    del batiment["quartier"]

    reponse = client.post("/predict", json=batiment, headers=EN_TETES)

    assert reponse.status_code == 422


def test_predict_refuse_un_champ_inconnu(client, batiment):
    batiment["couleur"] = "bleu"

    reponse = client.post("/predict", json=batiment, headers=EN_TETES)

    assert reponse.status_code == 422
