"""Colonnes communes aux bâtiments du dataset et aux entrées de prédiction."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class ChampsBatiment:
    """Les 11 champs métier d'un bâtiment, partagés par plusieurs tables.

    Un mixin : ses colonnes sont copiées dans chaque table qui en hérite, comme un trait en
    PHP. Les champs ne sont définis qu'une fois.
    """

    annee_construction: Mapped[int]
    nombre_batiments: Mapped[int]
    nombre_etages: Mapped[int]
    surface_batie: Mapped[float]
    surface_parking: Mapped[float]
    quartier: Mapped[str] = mapped_column(String(30))
    type_usage: Mapped[str] = mapped_column(String(50))
    nombre_usages: Mapped[int]
    part_usage_principal: Mapped[float]
    utilise_gaz: Mapped[bool]
    utilise_vapeur: Mapped[bool]
