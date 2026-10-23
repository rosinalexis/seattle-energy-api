"""Crée le rôle de l'API, les tables et les droits d'accès dans PostgreSQL.

Usage (depuis la racine du projet) : uv run python -m scripts.create_db
Se connecte avec le compte administrateur. Peut être relancé sans risque : ce qui existe déjà
est conservé.
"""

from psycopg import sql
from sqlalchemy import Connection, create_engine, make_url, text

import app.models  # noqa: F401 — enregistre les tables auprès de Base.metadata
from app.config import ReglagesAdmin
from app.database import Base

# Le strict nécessaire pour l'API : lire les bâtiments, lire et ajouter des prédictions.
# Ni UPDATE ni DELETE : même compromise, l'API ne peut pas falsifier l'historique.
DROITS_API = {
    "batiments": "SELECT",
    "prediction_entrees": "SELECT, INSERT",
    "prediction_sorties": "SELECT, INSERT",
}


def executer(connexion: Connection, requete: sql.Composed) -> None:
    """Exécute un ordre SQL composé avec psycopg.sql."""
    connexion.exec_driver_sql(requete.as_string())


def creer_role_api(connexion: Connection, role: str, mot_de_passe: str) -> None:
    """Crée le rôle de l'API, ou met à jour son mot de passe s'il existe déjà."""
    existe = connexion.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = :role"), {"role": role}
    ).first()
    ordre = (
        "ALTER ROLE {} WITH LOGIN PASSWORD {}"
        if existe
        else "CREATE ROLE {} WITH LOGIN PASSWORD {}"
    )
    # Un nom de rôle et un mot de passe ne peuvent pas être passés en paramètres d'un ordre
    # CREATE ROLE : psycopg.sql les échappe, ce qui empêche toute injection SQL.
    executer(connexion, sql.SQL(ordre).format(sql.Identifier(role), sql.Literal(mot_de_passe)))


def accorder_droits(connexion: Connection, role: str) -> None:
    """Donne au rôle de l'API uniquement les droits dont elle a besoin."""
    for table, droits in DROITS_API.items():
        executer(
            connexion,
            sql.SQL("GRANT {} ON {} TO {}").format(
                sql.SQL(droits), sql.Identifier(table), sql.Identifier(role)
            ),
        )
    # Les identifiants auto-incrémentés viennent de séquences : un INSERT doit pouvoir s'en servir.
    executer(
        connexion,
        sql.SQL("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {}").format(sql.Identifier(role)),
    )


def main() -> None:
    reglages = ReglagesAdmin()
    url_api = make_url(reglages.database_url)

    # begin() : une seule transaction, tout est créé ou rien ne l'est.
    with create_engine(reglages.database_admin_url).begin() as connexion:
        creer_role_api(connexion, url_api.username, url_api.password)
        Base.metadata.create_all(connexion)
        accorder_droits(connexion, url_api.username)

    print(f"Tables créées : {', '.join(Base.metadata.tables)}")
    print(
        f"Rôle de l'API : {url_api.username} ({', '.join(f'{t}: {d}' for t, d in DROITS_API.items())})"
    )


if __name__ == "__main__":
    main()
