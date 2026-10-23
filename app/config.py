"""Constantes, chemins et réglages du projet : une seule source de vérité."""

import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Calculé depuis l'emplacement de CE fichier, et non depuis le dossier courant :
# l'API, les scripts et les tests ne sont pas lancés depuis le même dossier.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Relevé 2016 de la ville de Seattle, jamais modifié.
RAW_DATA_FILE = PROJECT_ROOT / "data" / "raw" / "2016_Building_Energy_Benchmarking.csv"

# Produits par scripts/train_model.py : le modèle entraîné et ses scores sur le jeu de test.
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODEL_FILE = ARTIFACTS_DIR / "modele.joblib"
METRICS_FILE = ARTIFACTS_DIR / "metriques.json"

# Exemples d'entrées et de sorties du modèle, exportés depuis la base (livrable documenté).
EXEMPLES_FILE = PROJECT_ROOT / "docs" / "exemples" / "predictions.csv"

# Cible : la consommation brute relevée en 2016, en kBtu.
TARGET = "SiteEnergyUse(kBtu)"

# Année du relevé : sert à calculer l'âge des bâtiments.
ANNEE_RELEVE = 2016

# Fixée une fois pour toutes : sans graine, deux entraînements donnent deux modèles différents.
RANDOM_STATE = 42

# Lue dans pyproject.toml pour ne pas tenir la version à jour à deux endroits.
VERSION = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
    "version"
]


class Settings(BaseSettings):
    """Réglages propres à chaque environnement, lus dans les variables d'environnement.

    En local, ils viennent du fichier .env (jamais commité) ; en CI et en production, des
    secrets de l'environnement. Une variable obligatoire absente bloque le démarrage.
    """

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    # Clé que les clients envoient dans l'en-tête X-API-Key. 32 caractères minimum : une clé
    # vide (secret oublié) ou trop courte (devinable) empêche l'API de démarrer.
    api_key: str = Field(min_length=32)

    # Connexion de l'API à PostgreSQL, avec un rôle aux droits restreints (créé par
    # scripts/create_db.py) : jamais avec le compte administrateur.
    database_url: str


class ReglagesAdmin(BaseSettings):
    """Réglages des scripts d'administration de la base (création, chargement des données).

    Séparés de ceux de l'API : l'API ne reçoit jamais les identifiants administrateur.
    """

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    database_admin_url: str
    # L'URL de l'API indique le rôle restreint à créer et son mot de passe.
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Lit les réglages une seule fois."""
    return Settings()
