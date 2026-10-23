"""Prédit la consommation de bâtiments tirés de la base et la compare à leur consommation réelle.

Chaque prédiction passe par le même service que l'API : l'entrée et la sortie sont enregistrées,
reliées au bâtiment du dataset (batiment_id).

Usage (depuis la racine du projet) : uv run python -m scripts.predire_batiments [nombre]

Attention : 80 % des bâtiments du dataset ont servi à l'entraînement, l'écart affiché est donc
optimiste. La performance du modèle se lit dans artifacts/metriques.json (jeu de test).
"""

import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.ml.modele import charger_modele
from app.models import BatimentReleve
from app.schemas.prediction import Batiment
from app.services.prediction import predire_et_enregistrer

NOMBRE_PAR_DEFAUT = 5


def main(nombre: int) -> None:
    modele = charger_modele()
    # Connexion avec le rôle restreint de l'API : le script n'a pas plus de droits qu'elle.
    with Session(get_engine()) as session:
        releves = session.scalars(
            select(BatimentReleve).order_by(func.random()).limit(nombre)
        ).all()

        for releve in releves:
            # Passer par le schéma de l'API valide les données comme pour un vrai client.
            batiment = Batiment(
                **{champ: getattr(releve, champ) for champ in Batiment.model_fields}
            )
            sortie = predire_et_enregistrer(batiment, modele, session, batiment_id=releve.id)

            reel = releve.consommation_reelle_kbtu
            ecart = (sortie.consommation_kbtu - reel) / reel
            print(
                f"Bâtiment {releve.id:>5} | {releve.type_usage:<28} | "
                f"prédit {sortie.consommation_kbtu:>13,.0f} kBtu | réel {reel:>13,.0f} kBtu | "
                f"écart {ecart:+.0%} | prédiction n° {sortie.id}"
            )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else NOMBRE_PAR_DEFAUT)
