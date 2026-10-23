"""Tables de traçabilité : ce qui a été envoyé au modèle, et ce qu'il a répondu.

Deux tables plutôt qu'une : l'entrée est enregistrée avant l'appel au modèle, la sortie après.
Si le modèle échoue, l'entrée reste en base sans sortie : la tentative est tracée.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.champs import ChampsBatiment


class PredictionEntree(ChampsBatiment, Base):
    """Les données d'un bâtiment envoyées au modèle."""

    __tablename__ = "prediction_entrees"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Renseigné quand la prédiction porte sur un bâtiment du dataset : on peut alors comparer
    # la prédiction à la consommation réelle. Vide pour une requête d'un client de l'API.
    batiment_id: Mapped[int | None] = mapped_column(ForeignKey("batiments.id"), index=True)
    # Horodatage fourni par PostgreSQL : une seule horloge de référence. Indexé pour
    # interroger l'historique par période sans parcourir toute la table.
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    sortie: Mapped["PredictionSortie | None"] = relationship(back_populates="entree")


class PredictionSortie(Base):
    """La réponse du modèle pour une entrée."""

    __tablename__ = "prediction_sorties"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique : une entrée a au plus une sortie (relation 1-1).
    entree_id: Mapped[int] = mapped_column(ForeignKey("prediction_entrees.id"), unique=True)
    consommation_kbtu: Mapped[float]
    # Version de l'API, donc du modèle, qui a produit la prédiction : après un réentraînement,
    # on sait quel modèle a répondu quoi.
    version_modele: Mapped[str] = mapped_column(String(20))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entree: Mapped[PredictionEntree] = relationship(back_populates="sortie")
