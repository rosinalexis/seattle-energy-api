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

### Configuration

Les réglages propres à chaque environnement sont lus dans les variables d'environnement. En local,
copier le modèle et renseigner une vraie clé :

```bash
cp .env.example .env
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"   # à coller dans API_KEY
```

| Variable  | Rôle                                                     |
|-----------|----------------------------------------------------------|
| `API_KEY` | clé que les clients envoient dans l'en-tête `X-API-Key` (32 caractères minimum) |

Le fichier `.env` n'est jamais commité. Sans `API_KEY` valide, l'API refuse de démarrer.

## Utilisation

### 1. Entraîner le modèle

```bash
uv run python -m scripts.train_model
```

Le script reproduit le nettoyage et le modèle du projet 3 (random forest, 1 582 bâtiments), puis
écrit `artifacts/modele.joblib` et ses scores sur le jeu de test dans `artifacts/metriques.json`.
Le modèle n'est pas versionné : il se régénère à l'identique (données, code, versions et graine
aléatoire fixés).

| Métrique (317 bâtiments de test) | Valeur        |
|----------------------------------|---------------|
| R²                               | 0,711         |
| MAE                              | 3,75 M kBtu   |
| Erreur relative médiane          | 39,8 %        |

### 2. Lancer l'API

```bash
uv run uvicorn app.main:app --reload
```

Documentation interactive (Swagger) : <http://localhost:8000/docs>.

### 3. Appeler l'API

| Méthode | Route      | Authentification | Rôle                                         |
|---------|------------|------------------|----------------------------------------------|
| `GET`   | `/health`  | non              | vérifier que l'API répond                    |
| `POST`  | `/predict` | `X-API-Key`      | prédire la consommation annuelle d'un bâtiment |

```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: <votre clé>" \
  -H "Content-Type: application/json" \
  -d '{
    "annee_construction": 1927,
    "nombre_batiments": 1,
    "nombre_etages": 12,
    "surface_batie": 88434,
    "surface_parking": 0,
    "quartier": "DOWNTOWN",
    "type_usage": "Hotel",
    "nombre_usages": 1,
    "part_usage_principal": 1.0,
    "utilise_gaz": true,
    "utilise_vapeur": true
  }'
```

```json
{"consommation_kbtu": 7113386.17}
```

Codes de réponse :

| Code  | Cas                                                                          |
|-------|------------------------------------------------------------------------------|
| `200` | prédiction réussie                                                           |
| `401` | clé d'API absente ou invalide                                                |
| `422` | donnée invalide ou hors du domaine du modèle ; le message désigne le champ   |

Le domaine accepté reprend celui des données d'entraînement (13 quartiers, 23 types d'usage, années
1900 à 2016, 1 à 76 étages…) : en dehors, le modèle n'a jamais rien vu et sa prédiction ne vaudrait
rien. Le détail de chaque champ est dans Swagger.

## Déploiement

L'API est livrée sous forme d'**image Docker**, publiée automatiquement sur GitHub Container
Registry (GHCR) après chaque fusion dans une branche d'environnement :

| Branche | Environnement GitHub | Image                                                  |
|---------|----------------------|--------------------------------------------------------|
| `dev`   | `dev`                | `ghcr.io/rosinalexis/seattle-energy-api:dev`           |
| `test`  | `test`               | `ghcr.io/rosinalexis/seattle-energy-api:test`          |
| `main`  | `prod`               | `ghcr.io/rosinalexis/seattle-energy-api:prod`          |

Chaque image est aussi étiquetée avec le hash du commit dont elle est issue. Avant publication, la CI
lance l'image et l'appelle pour de vrai (test de fumée), avec la clé d'API de l'environnement.

Lancer la version de production sur n'importe quelle machine équipée de Docker :

```bash
docker run -d -p 8000:8000 --env-file .env ghcr.io/rosinalexis/seattle-energy-api:prod
```

Ou construire l'image en local :

```bash
docker build -t seattle-energy-api .
docker run -d -p 8000:8000 --env-file .env seattle-energy-api
```

L'image contient le modèle, entraîné pendant sa construction ; elle ne contient ni le `.env`, ni les
tests, ni les outils de développement. L'API y tourne sous un utilisateur sans privilèges, et Docker
surveille `/health` (healthcheck).

**Pourquoi pas d'hébergement en ligne ?** La piste naturelle, Hugging Face Spaces, exige désormais un
abonnement payant pour les Spaces Docker
([documentation, vérifiée le 23/10/2026](https://huggingface.co/docs/hub/spaces-overview)). Le
livrable de déploiement est donc l'image publiée : elle se lance à l'identique sur n'importe quel
hébergeur Docker.

## Sécurité

- **Authentification** par clé d'API dans l'en-tête `X-API-Key`, comparée en temps constant
  (`secrets.compare_digest`) pour empêcher de la deviner en mesurant les temps de réponse.
- **Clé robuste obligatoire** : une clé absente ou de moins de 32 caractères bloque le démarrage.
- **Secrets** hors du code : `.env` en local (ignoré par Git et par Docker), secrets des
  environnements GitHub `dev`, `test` et `prod` en CI, chacun limité à sa branche.
- **Conteneur sans privilèges** : l'API ne tourne pas en root.
- **Validation stricte des entrées** (Pydantic) : types, bornes, listes fermées, champs inconnus
  refusés.
- **CI en lecture seule** (`permissions: contents: read`).

## Structure du dépôt

```
seattle-energy-api/
├── app/          # code de l'API (architecture en couches)
│   ├── main.py       # création de l'application, routes de supervision
│   ├── config.py     # constantes, chemins et réglages (une seule source de vérité)
│   ├── securite.py   # authentification par clé d'API
│   ├── routers/      # endpoints HTTP (contrôleurs)
│   ├── schemas/      # contrats d'entrée et de sortie (Pydantic)
│   ├── services/     # logique métier, indépendante de HTTP
│   └── ml/           # préparation des données et pipeline du modèle
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
