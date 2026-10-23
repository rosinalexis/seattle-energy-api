"""Tests de la connexion de l'API à PostgreSQL et des droits de son rôle."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.database import get_session


def test_l_api_lit_les_batiments(session):
    session.execute(text("SELECT count(*) FROM batiments"))


@pytest.mark.parametrize(
    "requete",
    [
        "UPDATE prediction_sorties SET consommation_kbtu = 0",
        "DELETE FROM prediction_entrees",
        "DELETE FROM batiments",
        "INSERT INTO batiments (id) VALUES (-1)",
        "DROP TABLE prediction_sorties",
    ],
)
def test_le_role_de_l_api_ne_peut_pas_modifier_l_historique_ni_le_dataset(session, requete):
    # Même compromise, l'API ne peut ni falsifier les prédictions passées, ni toucher au dataset.
    with pytest.raises(ProgrammingError, match="permission denied|must be owner"):
        session.execute(text(requete))


def test_get_session_ouvre_puis_ferme_une_session():
    generateur = get_session()
    session = next(generateur)

    assert isinstance(session, Session)
    # Fin de la requête HTTP : FastAPI reprend le générateur, qui ferme la session.
    with pytest.raises(StopIteration):
        next(generateur)
