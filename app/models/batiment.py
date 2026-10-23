"""Table des bâtiments du dataset d'entraînement."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.champs import ChampsBatiment


class BatimentReleve(ChampsBatiment, Base):
    """Un des 1 582 bâtiments du relevé 2016 retenus après nettoyage."""

    __tablename__ = "batiments"

    # L'identifiant du relevé de Seattle (OSEBuildingID) plutôt qu'un numéro généré : on
    # retrouve le bâtiment dans le fichier source.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    consommation_reelle_kbtu: Mapped[float]
