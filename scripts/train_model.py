"""Entraîne le modèle sur le relevé 2016 et le sauvegarde avec ses scores.

Usage (depuis la racine du projet) : uv run python -m scripts.train_model
"""

import json

import joblib
import pandas as pd

from app.config import ARTIFACTS_DIR, METRICS_FILE, MODEL_FILE, RAW_DATA_FILE
from app.ml.donnees import preparer_donnees
from app.ml.modele import entrainer_et_evaluer


def main() -> None:
    X, y = preparer_donnees(pd.read_csv(RAW_DATA_FILE))
    pipeline, metriques = entrainer_et_evaluer(X, y)

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    joblib.dump(pipeline, MODEL_FILE)
    METRICS_FILE.write_text(json.dumps(metriques, indent=2), encoding="utf-8")

    print(f"Modèle sauvegardé : {MODEL_FILE}")
    print(json.dumps(metriques, indent=2))


if __name__ == "__main__":
    main()
