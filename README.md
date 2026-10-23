# Seattle Energy API

[![CI](https://github.com/rosinalexis/seattle-energy-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rosinalexis/seattle-energy-api/actions/workflows/ci.yml)

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

## Contribuer

Branches, commits, pull requests, pipeline CI et standards de code et d'expérimentation ML : voir
[CONTRIBUTING.md](CONTRIBUTING.md).

En résumé : une branche `<type>/<sujet>` par fonctionnalité, puis
`dev` (développement) → `test` (recette) → `main` (production, taguée), uniquement par pull request
validée par la CI.
