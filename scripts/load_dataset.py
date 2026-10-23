"""Charge les bâtiments du dataset nettoyé dans la table batiments.

Usage (depuis la racine du projet) : uv run python -m scripts.load_dataset
À lancer après scripts.create_db. Ne fait rien si la table contient déjà des bâtiments.
"""

import pandas as pd
from sqlalchemy import create_engine, func, select

from app.config import RAW_DATA_FILE, ReglagesAdmin
from app.ml.donnees import preparer_donnees
from app.models import BatimentReleve


def main() -> None:
    X, y = preparer_donnees(pd.read_csv(RAW_DATA_FILE))
    # L'index (OSEBuildingID) devient la colonne id, clé primaire de la table.
    batiments = X.assign(consommation_reelle_kbtu=y).rename_axis("id").reset_index()

    with create_engine(ReglagesAdmin().database_admin_url).begin() as connexion:
        deja_charges = connexion.execute(
            select(func.count()).select_from(BatimentReleve)
        ).scalar_one()
        # Relancer le script ne crée pas de doublons : un rechargement partiel laisserait
        # la table dans un état incohérent.
        if deja_charges:
            print(f"Table batiments déjà chargée ({deja_charges} bâtiments) : rien à faire.")
            return
        batiments.to_sql("batiments", connexion, if_exists="append", index=False)

    print(f"{len(batiments)} bâtiments chargés.")


if __name__ == "__main__":
    main()
