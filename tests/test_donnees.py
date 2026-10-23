"""Tests de la préparation du relevé brut."""

import numpy as np
import pandas as pd

from app.config import RAW_DATA_FILE
from app.ml.donnees import nombre_usages, part_usage_principal, preparer_donnees, type_usage
from app.schemas.prediction import Batiment


def test_nombre_usages_ignore_le_parking():
    df = pd.DataFrame({"ListOfAllPropertyUseTypes": ["Office, Parking"]})

    assert nombre_usages(df).iloc[0] == 1


def test_nombre_usages_ignore_les_virgules_entre_parentheses():
    df = pd.DataFrame(
        {
            "ListOfAllPropertyUseTypes": [
                "Repair Services (Vehicle, Shoe, Locksmith, etc), Retail Store"
            ]
        }
    )

    assert nombre_usages(df).iloc[0] == 2


def test_part_usage_principal_ignore_les_usages_absents():
    df = pd.DataFrame(
        {
            "LargestPropertyUseTypeGFA": [600],
            "SecondLargestPropertyUseTypeGFA": [400],
            "ThirdLargestPropertyUseTypeGFA": [np.nan],
        }
    )

    assert part_usage_principal(df).iloc[0] == 0.6


def test_type_usage_regroupe_les_categories_rares():
    df = pd.DataFrame(
        {
            "PrimaryPropertyType": ["Office", "Other", "Other"],
            "LargestPropertyUseType": ["Office", "Parking", "Fitness Center"],
        }
    )

    assert type_usage(df).tolist() == ["Small- and Mid-Sized Office", "Parking", "Other"]


def test_preparer_donnees_reproduit_le_nettoyage_du_projet_3():
    X, y = preparer_donnees(pd.read_csv(RAW_DATA_FILE))

    # 1 582 bâtiments à l'issue du nettoyage dans le notebook du projet 3.
    assert len(X) == len(y) == 1582
    assert not X.isna().any().any()
    # Le modèle s'entraîne exactement sur les champs que l'API reçoit.
    assert list(X.columns) == list(Batiment.model_fields)
