import pytest
from pydantic import ValidationError

from app.config import PROJECT_ROOT, RAW_DATA_FILE, Settings


def test_racine_du_projet_contient_pyproject():
    # Si la racine est mal calculée, tous les chemins qui en dépendent sont faux.
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_fichier_de_donnees_brutes_existe():
    # L'entraînement et l'insertion en base dépendent de ce fichier.
    assert RAW_DATA_FILE.exists()


def test_une_cle_d_api_trop_courte_est_refusee():
    # Une clé vide (secret oublié) ou courte (devinable) doit bloquer le démarrage.
    with pytest.raises(ValidationError):
        Settings(api_key="trop-courte")
