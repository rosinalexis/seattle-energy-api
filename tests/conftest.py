"""Fixtures partagées par tous les tests (pytest charge ce fichier automatiquement)."""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.ml.modele import charger_modele
from app.schemas.prediction import Batiment

CLE_TEST = "cle-de-test-assez-longue-pour-etre-acceptee"


@pytest.fixture
def client(monkeypatch):
    """Client HTTP de test, avec une clé d'API connue des tests."""
    # La clé de test prend le pas sur celle du .env : les tests ne dépendent pas de la machine.
    monkeypatch.setenv("API_KEY", CLE_TEST)
    get_settings.cache_clear()
    # Le with déclenche le démarrage de l'API (lifespan), comme en production.
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


@pytest.fixture
def en_tetes() -> dict:
    """En-têtes d'une requête authentifiée avec la clé de test."""
    return {"X-API-Key": CLE_TEST}


@pytest.fixture
def batiment() -> dict:
    """Un bâtiment valide : l'exemple affiché dans Swagger, pour ne pas le définir deux fois."""
    return dict(Batiment.model_config["json_schema_extra"]["examples"][0])


@pytest.fixture
def modele():
    """Le modèle entraîné par scripts/train_model.py."""
    return charger_modele()
