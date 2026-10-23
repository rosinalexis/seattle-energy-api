# Fiche du modèle

Prédiction de la consommation d'énergie annuelle des bâtiments non résidentiels de Seattle.

Sauf mention contraire, les chiffres sont **mesurés sur le modèle servi par l'API**, avec le même
découpage entraînement / test que le projet 3 (`random_state=42`). Ils se recalculent avec
`uv run python -m scripts.train_model`, qui écrit `artifacts/metriques.json`.

## 1. Usage prévu

| | |
|---|---|
| **Objectif** | estimer la consommation annuelle (kBtu) d'un bâtiment **sans relevé**, à partir de ce que l'on sait de lui : taille, usage, âge, quartier, raccordements |
| **Utilisateurs** | services de la ville, bureaux d'études : ordre de grandeur, priorisation des bâtiments à auditer |
| **Hors usage** | facturation, sanction, ou toute décision sur un bâtiment isolé : l'erreur typique est de 40 % (voir §4) |
| **Périmètre** | bâtiments **non résidentiels** de Seattle, comparables à ceux du relevé 2016 |

## 2. Données

**Source** : relevé de consommation 2016 de la ville de Seattle (*2016 Building Energy
Benchmarking*), fichier `data/raw/2016_Building_Energy_Benchmarking.csv`, jamais modifié.

**Préparation** (`app/ml/donnees.py`, reproduit à l'identique le notebook du projet 3) :

| Étape                                                              | Bâtiments |
|--------------------------------------------------------------------|----------:|
| Relevé brut                                                        | 3 376     |
| Non résidentiels uniquement                                        | 1 668     |
| Retrait des incohérences (aberrants signalés par la ville, consommation nulle, 0 étage, valeurs impossibles, logements déguisés, campus entier, sources d'énergie incohérentes) | 1 597 |
| Retrait des consommations anormales pour leur taille (z-score > 3 sur log de l'intensité) | **1 582** |

**Cible** : `SiteEnergyUse(kBtu)`, la consommation brute relevée.

**Les 11 champs d'entrée**, identiques dans l'API, la base et l'entraînement :

| Champ                  | Type        | Remarque                                           |
|------------------------|-------------|----------------------------------------------------|
| `annee_construction`   | entier      | transformé en âge (2016 − année) dans le pipeline  |
| `nombre_batiments`     | entier      |                                                    |
| `nombre_etages`        | entier      | sert aussi à la surface par étage                  |
| `surface_batie`        | sf          | sert aussi à la surface par étage                  |
| `surface_parking`      | sf          |                                                    |
| `quartier`             | 13 valeurs  | libellés harmonisés                                |
| `type_usage`           | 23 valeurs  | types de la ville, regroupés pour avoir assez d'exemples par catégorie |
| `nombre_usages`        | entier      | parking exclu                                      |
| `part_usage_principal` | 0 à 1       | part de la surface d'usage                         |
| `utilise_gaz`          | booléen     | présence seulement, jamais la quantité             |
| `utilise_vapeur`       | booléen     | présence seulement, jamais la quantité             |

**Data leakage écarté** : toutes les colonnes calculées à partir de la consommation (intensités,
ENERGY STAR Score, électricité et gaz consommés, émissions) sont exclues. Seule la *présence* du gaz
et de la vapeur est utilisée : elle se connaît sans relevé.

## 3. Modèle

Un **pipeline scikit-learn** unique, sauvegardé tel quel (`artifacts/modele.joblib`) :

```
champs métier ──► features dérivées ──► préparation des colonnes ──► random forest ──► kBtu
                  (âge, surface         (one-hot : type, quartier ;
                   par étage)            standardisation : numériques ;
                                         booléens tels quels)
```

L'API donne au pipeline les champs bruts : il applique lui-même toutes les transformations de
l'entraînement. Aucune transformation n'est dupliquée entre l'entraînement et la production.

| Hyperparamètre     | Valeur | |
|--------------------|--------|---|
| `n_estimators`     | 200    | nombre d'arbres |
| `max_depth`        | aucune | arbres développés jusqu'au bout |
| `min_samples_leaf` | 1      | |
| `max_features`     | 0,5    | chaque division ne considère que la moitié des features |
| `random_state`     | 42     | reproductibilité |

**Pourquoi ce modèle** (projet 3) : 5 modèles comparés (référence naïve, régression linéaire, SVR,
random forest, XGBoost). Les deux modèles à arbres ont été optimisés par GridSearch (180
combinaisons pour le random forest, 144 pour XGBoost), puis départagés sur 50 découpages : le random
forest gagne la majorité des tours sur les 4 métriques et il est plus stable.

## 4. Performances

Jeu de test : **317 bâtiments** (20 %) jamais vus pendant l'entraînement.

| Métrique                    | Test          | Entraînement | Lecture                                               |
|-----------------------------|---------------|--------------|-------------------------------------------------------|
| R²                          | **0,711**     | 0,965        | 71 % de la variance de la consommation est expliquée  |
| Erreur relative médiane     | **39,8 %**    | 14,7 %       | pour un bâtiment typique, la prédiction s'écarte d'environ 40 % |
| MAE                         | 3,75 M kBtu   |              | erreur absolue moyenne, tirée par les gros bâtiments  |
| Erreur absolue médiane      | 1,2 M kBtu    |              | pour une consommation médiane de 2,69 M kBtu          |
| RMSE                        | 10,8 M kBtu   |              | très supérieure à la MAE : quelques très grosses erreurs |

**Où se trompe-t-il ?**

- **Les gros consommateurs concentrent l'erreur** : les 10 % plus gros bâtiments du test produisent
  **54,8 %** de l'erreur absolue totale.
- **Erreurs fortes** : 58 bâtiments de test sur 317 (18 %) ont une erreur relative supérieure à
  100 %.
- **La taille ne change pas l'erreur relative** : 41 % pour le tiers le plus petit, 39 % pour le
  tiers moyen et pour le tiers le plus grand.
- **Sur-apprentissage** : R² de 0,965 en entraînement contre 0,711 en test. Les arbres sans
  profondeur maximale mémorisent une partie des bâtiments d'entraînement ; la GridSearch a malgré
  tout retenu ce réglage, le meilleur en validation croisée.

**Ce qui pèse dans les prédictions** (importance des features du random forest, en % du total) :

| Feature               | Importance | Feature                | Importance |
|-----------------------|-----------:|------------------------|-----------:|
| `surface_batie`       | 39,5 %     | `age_batiment`         | 3,2 %      |
| `type_usage`          | 19,8 %     | `utilise_vapeur`       | 2,6 %      |
| `nombre_batiments`    | 9,3 %      | `surface_parking`      | 2,5 %      |
| `nombre_etages`       | 7,3 %      | `part_usage_principal` | 2,4 %      |
| `surface_par_etage`   | 6,8 %      | `nombre_usages`        | 1,0 %      |
| `quartier`            | 5,3 %      | `utilise_gaz`          | 0,2 %      |

La taille puis l'usage expliquent l'essentiel, comme l'exploration du projet 3 l'avait montré.
Cette importance (fondée sur l'impureté des arbres) favorise les variables continues : c'est un
ordre de grandeur, pas une mesure causale.

## 5. Limites et biais

- **Une seule année, une seule ville** : le modèle a appris sur le relevé 2016 de Seattle. Les
  bâtiments récents, les autres climats et l'évolution des usages ne sont pas représentés.
- **Domaine borné** : l'API refuse ce qui sort du domaine d'entraînement (années 1900 à 2016, 1 à
  76 étages, 13 quartiers, 23 types d'usage…). Dans ce domaine, les catégories rares (10 hôpitaux,
  9 laboratoires) restent moins bien apprises.
- **Erreur typique de 40 %** : un ordre de grandeur, pas une mesure. À ne pas utiliser pour une
  décision sur un bâtiment isolé.
- **Consommation, pas émissions** : le modèle ne prédit pas le CO2 (dans le projet 3, le même modèle
  n'expliquait qu'environ un tiers de la variance des émissions en validation croisée).

**Piste d'amélioration mesurée** (projet 3) : une régression linéaire sur les logarithmes de la
surface et de la consommation (« log-log ») ramène l'erreur relative médiane à environ 36 % contre
41 % pour le random forest, sur les mêmes 50 découpages. Elle n'a pas été évaluée sur le jeu de test,
réservé au modèle final.

## 6. Maintenance

### Ce qui est versionné

| Élément                       | Où                                               |
|-------------------------------|--------------------------------------------------|
| Code, données, hyperparamètres | Git (le modèle se régénère à l'identique)       |
| Versions des bibliothèques    | `uv.lock`                                        |
| Modèle en service             | image Docker GHCR, étiquetée par commit et par environnement |
| Version qui a produit chaque prédiction | colonne `version_modele` de `prediction_sorties` |

### Surveillance

Toutes les prédictions sont tracées en base. Les requêtes de `scripts/requetes.sql` permettent de
suivre :

- les **tentatives sans réponse** du modèle (entrée sans sortie) ;
- le **volume** de prédictions par jour et par version ;
- l'**écart à la réalité** dès que la consommation réelle d'un bâtiment prédit est connue.

### Quand réentraîner

- **Chaque année**, à la publication d'un nouveau relevé de consommation par la ville ;
- quand l'erreur mesurée sur des bâtiments dont la consommation réelle est connue dérive nettement
  au-delà de 40 % ;
- quand les clients demandent des bâtiments hors du domaine actuel (nouveaux types, bâtiments
  récents).

### Protocole de mise à jour

1. **Données** : ajouter le nouveau relevé dans `data/raw/` (l'ancien reste intact) et adapter
   `app/ml/donnees.py` si le format a changé.
2. **Configuration** : mettre à jour `ANNEE_RELEVE` (`app/config.py`) et, si le domaine change,
   les bornes et les listes du schéma (`app/schemas/prediction.py`). Un test vérifie que les
   catégories acceptées par l'API sont exactement celles apprises par le modèle.
3. **Réentraîner** : `uv run python -m scripts.train_model`, et comparer `artifacts/metriques.json`
   aux performances du modèle en service.
4. **Valider** : `uv run pytest`. Les tests imposent un plancher de performance
   (`tests/unit/ml/test_entrainement.py` : R² ≥ 0,70, erreur relative médiane ≤ 40 %) : **un modèle
   moins bon ne peut pas partir en production**. Ajuster ce plancher seulement si le nouveau modèle
   fait mieux.
5. **Livrer** : branche `feat/…`, pull request vers `dev`, puis `test`, puis `main`, en passant la
   version (`pyproject.toml`) au numéro suivant. La CI réentraîne, teste, construit l'image et la
   vérifie avant publication.
6. **Retour arrière** : chaque image publiée reste disponible sous l'étiquette de son commit. Pour
   revenir à une version précédente : `IMAGE_TAG=<hash complet du commit> docker compose up -d api`
   (`git log --format=%H main` liste les hash).
