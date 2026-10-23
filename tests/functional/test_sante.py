"""Tests fonctionnels de GET /health."""


def test_health_repond_sans_authentification(client):
    reponse = client.get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}
