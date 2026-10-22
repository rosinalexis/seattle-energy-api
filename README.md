# Seattle Energy API

API de prédiction de la consommation d'énergie des bâtiments non résidentiels de Seattle.

Ce projet met en production le modèle de machine learning du projet 3 (random forest entraîné sur le
relevé 2016 de la ville de Seattle) : exposition via une API FastAPI, traçabilité des prédictions en
base PostgreSQL, tests automatisés et pipeline CI/CD.

> Contexte : projet 5 du parcours AI Engineer d'OpenClassrooms, réalisé pour le client fictif Futurisys.

## Installation

Prérequis : [uv](https://docs.astral.sh/uv/) et Git.

```bash
git clone https://github.com/rosinalexis/seattle-energy-api.git
cd seattle-energy-api
uv sync
```

`uv sync` installe la bonne version de Python (fixée dans `.python-version`) et les dépendances aux
versions exactes de `uv.lock`.

### Dépendances

Les dépendances sont déclarées dans `pyproject.toml` et figées dans `uv.lock` : ces deux fichiers
remplacent le `requirements.txt`. Si un outil en exige un, on le génère depuis le lock :

```bash
uv export --format requirements-txt > requirements.txt
```

## Structure du dépôt

```
seattle-energy-api/
├── app/          # code de l'API (architecture en couches)
├── scripts/      # scripts lancés à la main : entraînement, création de la base…
├── tests/        # tests unitaires et fonctionnels
├── data/raw/     # relevé 2016 de Seattle, jamais modifié
├── artifacts/    # modèle entraîné, produit par le script d'entraînement
└── docs/         # documentation technique et schéma de la base
```

## Conventions Git

### Branches

Le projet suit le **GitLab Flow** : une branche longue par environnement, et une branche courte par
fonctionnalité.

| Branche  | Environnement | Rôle                                          |
|----------|---------------|-----------------------------------------------|
| `main`   | production    | version livrée, taguée                        |
| `test`   | test          | recette : la suite de tests complète y tourne |
| `dev`    | développement | intégration des fonctionnalités               |

Les branches de travail partent de `dev` et sont nommées `<type>/<sujet-court>`, avec les mêmes types
que les commits :

```
feat/api-prediction
ci/pipeline-tests
docs/schema-base
```

Le code avance toujours dans le même sens, uniquement par pull request :

```
<type>/<sujet>  →  dev  →  test  →  main
```

Aucun push direct sur `dev`, `test` ou `main`.

### Commits

Les messages suivent les [Conventional Commits](https://www.conventionalcommits.org/fr/) :

```
<type>: <description courte, au présent>
```

| Type       | Usage                                        |
|------------|----------------------------------------------|
| `feat`     | nouvelle fonctionnalité                      |
| `fix`      | correction de bug                            |
| `test`     | ajout ou modification de tests               |
| `docs`     | documentation uniquement                     |
| `ci`       | pipeline CI/CD                               |
| `refactor` | réécriture sans changement de comportement   |
| `chore`    | configuration, dépendances, outillage        |

Exemple : `feat: ajoute l'endpoint de prédiction`

### Versions

Chaque fusion dans `main` reçoit un tag [SemVer](https://semver.org/lang/fr/) `vMAJEUR.MINEUR.CORRECTIF`
(`v0.1.0`, `v0.2.0`…). La version `v1.0.0` correspond à la livraison finale.
