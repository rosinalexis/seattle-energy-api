"""Tests du démarrage de l'API : elle refuse de démarrer s'il lui manque quelque chose."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.database import get_engine
from app.main import app
from app.ml.modele import charger_modele


@pytest.fixture
def caches_vides():
    """Vide les caches avant et après le test : les autres tests retrouvent la vraie config."""
    for fonction in (get_settings, get_engine, charger_modele):
        fonction.cache_clear()
    yield
    for fonction in (get_settings, get_engine, charger_modele):
        fonction.cache_clear()


def test_l_api_refuse_de_demarrer_sans_modele(monkeypatch, tmp_path, caches_vides):
    monkeypatch.setattr("app.ml.modele.MODEL_FILE", tmp_path / "absent.joblib")

    with pytest.raises(FileNotFoundError), TestClient(app):
        pass


def test_l_api_refuse_de_demarrer_si_la_base_refuse_la_connexion(monkeypatch, caches_vides):
    # De mauvais identifiants font échouer la connexion instantanément. Une base éteinte
    # aussi, mais après le délai de connexion (DELAI_CONNEXION) : le test serait lent.
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://inconnu:mauvais@127.0.0.1:5432/seattle_energy"
    )

    with pytest.raises(OperationalError), TestClient(app):
        pass
