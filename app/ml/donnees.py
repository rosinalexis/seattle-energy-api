"""Préparation du relevé brut pour l'entraînement.

Reproduit le nettoyage et le feature engineering du notebook du projet 3, dans le même ordre :
certaines étapes (détection des aberrants) dépendent des lignes encore présentes.
Le résultat est exprimé avec les champs métier de l'API, pour que le modèle reçoive à
l'entraînement exactement les mêmes colonnes qu'en production.
"""

import numpy as np
import pandas as pd

from app.config import TARGET

# Le relevé couvre aussi les logements collectifs : seuls les non résidentiels sont étudiés.
TYPES_NON_RESIDENTIELS = [
    "NonResidential",
    "Nonresidential COS",
    "Nonresidential WA",
    "SPS-District K-12",
    "Campus",
]

# "Entire Campus" : un campus entier déclaré comme un seul bâtiment de 2 étages.
# Ciblé par son identifiant, stable, plutôt que par un numéro de ligne.
ID_CAMPUS_ENTIER = 22062

# Usages de la catégorie fourre-tout "Other" dont l'intensité médiane s'écarte nettement
# du reste (mesuré dans le notebook du projet 3) : ils deviennent leur propre catégorie.
USAGES_SORTIS_DE_OTHER = [
    "Other - Recreation",
    "Other - Entertainment/Public Assembly",
    "Parking",
]

# Seuil de détection des bâtiments à la consommation anormale pour leur taille.
SEUIL_ZSCORE = 3


def nettoyer(releve: pd.DataFrame) -> pd.DataFrame:
    """Retire les bâtiments hors périmètre ou incohérents, et corrige les erreurs certaines."""
    df = releve[releve["BuildingType"].isin(TYPES_NON_RESIDENTIELS)].copy()

    # Bâtiments signalés aberrants par la ville elle-même.
    df = df[df["Outlier"].isna()]

    # Sans consommation valide, la ligne ne peut pas servir à l'entraînement.
    df = df[df[TARGET] > 0]

    # Une propriété a au moins un bâtiment : 0 est une erreur de saisie.
    df.loc[df["NumberofBuildings"] == 0, "NumberofBuildings"] = 1

    # Un nombre d'étages manquant ne se devine pas.
    df = df[df["NumberofFloors"] > 0]

    # Église à 99 étages (plus haut que la plus haute tour de Seattle), campus géants,
    # bâtiment à émissions négatives : valeurs impossibles ou uniques.
    extremes = (
        (df["NumberofFloors"] > 76) | (df["NumberofBuildings"] > 50) | (df["TotalGHGEmissions"] < 0)
    )
    df = df[~extremes]

    # Un usage secondaire déclaré à 0 sf n'en est pas un (le parking est déjà compté à part).
    for rang in ["Second", "Third"]:
        colonnes = [f"{rang}LargestPropertyUseType", f"{rang}LargestPropertyUseTypeGFA"]
        df.loc[df[colonnes[1]] == 0, colonnes] = None

    # Usage principal inconnu : aucune valeur sûre à mettre.
    df = df.dropna(subset=["LargestPropertyUseType"])

    # Même quartier écrit de plusieurs façons.
    df["Neighborhood"] = (
        df["Neighborhood"].str.upper().replace("DELRIDGE NEIGHBORHOODS", "DELRIDGE")
    )

    # Usage principal résidentiel : hors périmètre malgré le type NonResidential.
    residentiel = (df["PrimaryPropertyType"] == "Low-Rise Multifamily") | (
        df["LargestPropertyUseType"] == "Multifamily Housing"
    )
    df = df[~residentiel]

    df = df[df["OSEBuildingID"] != ID_CAMPUS_ENTIER]

    # Ventilation des sources incohérente (un restaurant sans électricité…) : la présence
    # du gaz et de la vapeur ne peut pas être établie de façon fiable.
    return df[df["Electricity(kBtu)"] != 0]


def nombre_usages(df: pd.DataFrame) -> pd.Series:
    """Nombre d'usages déclarés, hors parking."""
    # Les parenthèses contiennent parfois des virgules ("Repair Services (Vehicle, Shoe…)") :
    # on les retire avant de découper, sinon un usage compterait pour plusieurs.
    usages = df["ListOfAllPropertyUseTypes"].str.replace(r"\s*\([^)]*\)", "", regex=True)
    # Le parking n'est pas un usage : sa surface est déjà dans PropertyGFAParking.
    a_parking = df["ListOfAllPropertyUseTypes"].str.contains("Parking", regex=False)
    return usages.str.split(", ").str.len() - a_parking.astype(int)


def part_usage_principal(df: pd.DataFrame) -> pd.Series:
    """Part de la surface d'usage occupée par l'usage principal (entre 0 et 1)."""
    # Dénominateur : la somme des surfaces d'usage déclarées, et non la surface bâtie,
    # que les déclarations dépassent parfois (la part dépasserait alors 100 %).
    surfaces = df[
        [
            "LargestPropertyUseTypeGFA",
            "SecondLargestPropertyUseTypeGFA",
            "ThirdLargestPropertyUseTypeGFA",
        ]
    ].sum(axis=1)
    return df["LargestPropertyUseTypeGFA"] / surfaces


def type_usage(df: pd.DataFrame) -> pd.Series:
    """Type d'usage principal, regroupé pour que chaque catégorie ait assez d'exemples."""
    types = df["PrimaryPropertyType"].replace({"Office": "Small- and Mid-Sized Office"})
    sortis = (df["PrimaryPropertyType"] == "Other") & df["LargestPropertyUseType"].isin(
        USAGES_SORTIS_DE_OTHER
    )
    return types.mask(sortis, df["LargestPropertyUseType"])


def vers_champs_metier(df: pd.DataFrame) -> pd.DataFrame:
    """Traduit les colonnes du relevé en champs métier, ceux que reçoit l'API."""
    return pd.DataFrame(
        {
            "annee_construction": df["YearBuilt"],
            "nombre_batiments": df["NumberofBuildings"],
            "nombre_etages": df["NumberofFloors"],
            "surface_batie": df["PropertyGFABuilding(s)"],
            "surface_parking": df["PropertyGFAParking"],
            "quartier": df["Neighborhood"],
            "type_usage": type_usage(df),
            "nombre_usages": nombre_usages(df),
            "part_usage_principal": part_usage_principal(df),
            # Seule la présence de la source est utilisée, jamais sa quantité : la quantité
            # consommée est une partie de la réponse (data leakage).
            "utilise_gaz": df["NaturalGas(kBtu)"] > 0,
            "utilise_vapeur": df["SteamUse(kBtu)"] > 0,
        },
        index=df.index,
    )


def consommation_anormale(df: pd.DataFrame) -> pd.Series:
    """Repère les bâtiments dont la consommation par pied carré est anormale (z-score > 3).

    En échelle log, l'intensité énergétique forme une cloche : le z-score en isole les queues.
    """
    intensite_log = np.log10(df[TARGET] / df["PropertyGFATotal"])
    zscore = (intensite_log - intensite_log.mean()) / intensite_log.std()
    return zscore.abs() > SEUIL_ZSCORE


def preparer_donnees(releve: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Du relevé brut aux données d'entraînement : (champs métier, consommation).

    Les lignes sont indexées par l'identifiant du bâtiment dans le relevé (OSEBuildingID),
    qui sert aussi de clé primaire en base.
    """
    df = nettoyer(releve)
    df = df[~consommation_anormale(df)].set_index("OSEBuildingID")
    return vers_champs_metier(df), df[TARGET]
