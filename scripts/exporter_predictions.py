"""Exporte l'historique des prédictions en CSV : chaque entrée avec sa sortie.

Usage (depuis la racine du projet) : uv run python -m scripts.exporter_predictions [fichier]
Par défaut, écrit docs/exemples/predictions.csv.
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.config import EXEMPLES_FILE
from app.database import get_engine

# LEFT JOIN : une entrée sans sortie (le modèle a échoué) apparaît quand même, avec une
# prédiction vide. La consommation réelle n'existe que pour les bâtiments du dataset.
REQUETE = """
SELECT
    e.id AS entree_id,
    e.cree_le,
    e.batiment_id,
    e.annee_construction, e.nombre_batiments, e.nombre_etages,
    e.surface_batie, e.surface_parking, e.quartier, e.type_usage,
    e.nombre_usages, e.part_usage_principal, e.utilise_gaz, e.utilise_vapeur,
    s.id AS sortie_id,
    s.consommation_kbtu AS consommation_predite_kbtu,
    s.version_modele,
    b.consommation_reelle_kbtu
FROM prediction_entrees AS e
LEFT JOIN prediction_sorties AS s ON s.entree_id = e.id
LEFT JOIN batiments AS b ON b.id = e.batiment_id
ORDER BY e.id
"""


def main(fichier: Path) -> None:
    with get_engine().connect() as connexion:
        # Int64 (avec majuscule) : entier qui accepte les vides. Sans lui, pandas convertirait
        # la colonne en décimaux (19928.0) dès qu'une prédiction de client n'a pas de bâtiment.
        predictions = pd.read_sql(text(REQUETE), connexion, dtype={"batiment_id": "Int64"})

    fichier.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(fichier, index=False)
    print(f"{len(predictions)} prédictions exportées dans {fichier}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else EXEMPLES_FILE)
