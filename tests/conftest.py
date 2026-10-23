"""Fixtures partagées par tous les tests (pytest charge ce fichier automatiquement)."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_engine, get_session
from app.main import app
from app.ml.modele import charger_modele
from app.schemas.prediction import Batiment

CLE_TEST = "cle-de-test-assez-longue-pour-etre-acceptee"

# Fixée avant tout test : elle prend le pas sur celle du .env, et la CI n'a pas besoin de la
# vraie clé. Les tests ne dépendent pas de la machine.
os.environ["API_KEY"] = CLE_TEST


@pytest.fixture
def session():
    """Session PostgreSQL dont tout le travail est annulé à la fin du test.

    Le test s'exécute dans une transaction jamais validée : la base reste intacte et chaque
    test repart du même état. Les commit() du code testé deviennent des points de sauvegarde
    à l'intérieur de cette transaction.
    """
    connexion = get_engine().connect()
    transaction = connexion.begin()
    session = Session(bind=connexion, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connexion.close()


@pytest.fixture
def client(session):
    """Client HTTP de test, dont les requêtes passent par la session annulée en fin de test."""
    # Les routes reçoivent la session du test au lieu d'en ouvrir une nouvelle.
    app.dependency_overrides[get_session] = lambda: session
    # Le with déclenche le démarrage de l'API (lifespan), comme en production.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


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


class ModeleEnPanne:
    """Faux modèle qui échoue à chaque prédiction, pour tester les scénarios d'erreur."""

    def predict(self, donnees):
        raise RuntimeError("panne du modèle")


@pytest.fixture
def modele_en_panne() -> ModeleEnPanne:
    return ModeleEnPanne()
