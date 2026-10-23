"""Constantes et chemins du projet : une seule source de vérité."""

from pathlib import Path

# Calculé depuis l'emplacement de CE fichier, et non depuis le dossier courant :
# l'API, les scripts et les tests ne sont pas lancés depuis le même dossier.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Relevé 2016 de la ville de Seattle, jamais modifié.
RAW_DATA_FILE = PROJECT_ROOT / "data" / "raw" / "2016_Building_Energy_Benchmarking.csv"
