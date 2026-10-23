"""Tables de la base.

Importer les modèles ici les enregistre tous auprès de Base.metadata : create_all() connaît
alors toutes les tables, quel que soit le module qui l'appelle.
"""

from app.models.batiment import BatimentReleve
from app.models.prediction import PredictionEntree, PredictionSortie

__all__ = ["BatimentReleve", "PredictionEntree", "PredictionSortie"]
