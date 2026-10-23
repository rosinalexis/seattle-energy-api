"""Connexion à PostgreSQL via SQLAlchemy."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings


class Base(DeclarativeBase):
    """Classe mère des tables : SQLAlchemy y recense toutes les tables du projet."""


@lru_cache
def get_engine() -> Engine:
    """Moteur de connexion, créé une seule fois : il gère un pool de connexions réutilisées."""
    # pool_pre_ping : vérifie qu'une connexion du pool est encore vivante avant de s'en
    # servir (la base a pu redémarrer entre deux requêtes).
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Ouvre une session par requête HTTP et la ferme à la fin, même en cas d'erreur."""
    with Session(get_engine()) as session:
        yield session
