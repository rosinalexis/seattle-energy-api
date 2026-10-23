"""Contrat d'entrée et de sortie de l'endpoint de prédiction.

Les bornes reprennent le domaine des données d'entraînement : en dehors, le modèle n'a jamais
rien vu et sa prédiction ne vaudrait rien. Mieux vaut refuser la requête que mal répondre.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import ANNEE_RELEVE

# Les 13 quartiers du relevé, après harmonisation des libellés.
Quartier = Literal[
    "BALLARD",
    "CENTRAL",
    "DELRIDGE",
    "DOWNTOWN",
    "EAST",
    "GREATER DUWAMISH",
    "LAKE UNION",
    "MAGNOLIA / QUEEN ANNE",
    "NORTH",
    "NORTHEAST",
    "NORTHWEST",
    "SOUTHEAST",
    "SOUTHWEST",
]

# Les 23 types d'usage principal appris par le modèle.
TypeUsage = Literal[
    "Distribution Center",
    "Hospital",
    "Hotel",
    "K-12 School",
    "Laboratory",
    "Large Office",
    "Medical Office",
    "Mixed Use Property",
    "Other",
    "Other - Entertainment/Public Assembly",
    "Other - Recreation",
    "Parking",
    "Refrigerated Warehouse",
    "Residence Hall",
    "Restaurant",
    "Retail Store",
    "Self-Storage Facility",
    "Senior Care Community",
    "Small- and Mid-Sized Office",
    "Supermarket / Grocery Store",
    "University",
    "Warehouse",
    "Worship Facility",
]


class Batiment(BaseModel):
    """Ce que l'on sait d'un bâtiment non résidentiel de Seattle sans relever sa consommation."""

    # Un champ inconnu est une erreur du client (faute de frappe) : on le signale au lieu de
    # l'ignorer en silence.
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "annee_construction": 1927,
                    "nombre_batiments": 1,
                    "nombre_etages": 12,
                    "surface_batie": 88434,
                    "surface_parking": 0,
                    "quartier": "DOWNTOWN",
                    "type_usage": "Hotel",
                    "nombre_usages": 1,
                    "part_usage_principal": 1.0,
                    "utilise_gaz": True,
                    "utilise_vapeur": True,
                }
            ]
        },
    )

    annee_construction: int = Field(
        ge=1900,
        le=ANNEE_RELEVE,
        description="Année de construction (le modèle est entraîné sur le relevé 2016).",
    )
    nombre_batiments: int = Field(ge=1, le=50, description="Nombre de bâtiments de la propriété.")
    # 76 : la plus haute tour de Seattle.
    nombre_etages: int = Field(ge=1, le=76, description="Nombre d'étages hors sol.")
    surface_batie: float = Field(gt=0, description="Surface bâtie, en pieds carrés (sf).")
    surface_parking: float = Field(ge=0, description="Surface de parking, en pieds carrés (sf).")
    quartier: Quartier = Field(description="Quartier de Seattle.")
    type_usage: TypeUsage = Field(description="Type d'usage principal du bâtiment.")
    nombre_usages: int = Field(ge=1, description="Nombre d'usages différents, parking exclu.")
    part_usage_principal: float = Field(
        gt=0, le=1, description="Part de la surface d'usage occupée par l'usage principal (0 à 1)."
    )
    utilise_gaz: bool = Field(description="Le bâtiment est-il raccordé au gaz ?")
    utilise_vapeur: bool = Field(description="Le bâtiment est-il raccordé au réseau de vapeur ?")


class Prediction(BaseModel):
    """Réponse de l'endpoint de prédiction."""

    consommation_kbtu: float = Field(
        description="Consommation d'énergie annuelle prédite, en kBtu."
    )
