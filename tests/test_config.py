from app.config import PROJECT_ROOT, RAW_DATA_FILE


def test_racine_du_projet_contient_pyproject():
    # Si la racine est mal calculée, tous les chemins qui en dépendent sont faux.
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_fichier_de_donnees_brutes_existe():
    # L'entraînement et l'insertion en base dépendent de ce fichier.
    assert RAW_DATA_FILE.exists()
