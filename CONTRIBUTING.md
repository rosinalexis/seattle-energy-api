# Standards du projet

Ce document fixe les règles de travail du dépôt : Git, intégration continue, code et expérimentation
ML. Toute contribution doit les respecter ; la CI en vérifie une partie automatiquement.

## Git

### Branches

Le projet suit le **GitLab Flow** : une branche longue par environnement, et une branche courte par
fonctionnalité.

| Branche  | Environnement | Rôle                                          |
|----------|---------------|-----------------------------------------------|
| `main`   | production    | version livrée, taguée                        |
| `test`   | test          | recette avant mise en production              |
| `dev`    | développement | intégration des fonctionnalités               |

Les branches de travail partent de `dev` et sont nommées `<type>/<sujet-court>`, avec les mêmes types
que les commits :

```
feat/api-prediction
ci/pipeline-qualite
docs/schema-base
```

Exception : les branches de tests sont préfixées **`tests/`** et non `test/`. Git range les branches
comme des fichiers : tant que la branche d'environnement `test` existe, il ne peut pas exister de
« dossier » `test/`.

Le code avance toujours dans le même sens, uniquement par pull request :

```
<type>/<sujet>  →  dev  →  test  →  main
```

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

Un commit = un changement cohérent. Exemple : `feat: ajoute l'endpoint de prédiction`.

### Pull requests

- Une PR de fonctionnalité porte le titre de son changement principal, au format des commits.
- Une PR de promotion entre environnements s'appelle `chore: promotion dev → test` ou
  `chore: promotion test → main`.
- Fusion par **merge commit** uniquement : le squash et le rebase réécriraient les commits, et les
  branches d'environnement n'auraient plus d'historique commun.

### Versions

Chaque fusion dans `main` reçoit un tag [SemVer](https://semver.org/lang/fr/)
`vMAJEUR.MINEUR.CORRECTIF`. La version `v1.0.0` correspond à la livraison finale.

## Intégration continue

Le workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) lance le job `quality` :

| Déclencheur                            | Ce qui est testé                                   |
|----------------------------------------|----------------------------------------------------|
| `push` sur n'importe quelle branche    | la branche telle quelle (retour rapide)            |
| `pull_request` vers `dev`, `test`, `main` | le résultat de la fusion dans la branche cible |

Étapes du job : installation exacte depuis `uv.lock`, lint `ruff`, vérification du formatage, tests
`pytest` avec rapport de couverture.

Règles appliquées sur `dev`, `test` et `main` (ruleset GitHub) :

- pas de push direct : tout passe par une pull request ;
- le check `quality (pull_request)` doit être vert pour fusionner : c'est lui qui teste le résultat
  de la fusion (le check `quality (push)` ne teste que la branche seule) ;
- pas de suppression de branche ni de réécriture d'historique (force push) ;
- fusion par merge commit uniquement.

Les PR vers `dev` et `test` peuvent être fusionnées automatiquement dès que la CI est verte
(auto-merge). Le passage `test → main` reste une décision humaine : c'est la mise en production.

Chaque branche longue correspond à un **environnement GitHub** (`dev`, `test`, `prod`), qui porte ses
propres secrets et n'accepte de déploiement que depuis sa branche.

Après une fusion dans `dev`, `test` ou `main`, et seulement si `quality` est vert, le job `deploy` :

1. construit l'image Docker (le modèle y est entraîné) ;
2. la lance et l'appelle pour de vrai (test de fumée), avec la clé d'API de l'environnement ;
3. la publie sur GHCR, étiquetée avec le hash du commit et le nom de l'environnement.

## Code

- **Lint et formatage** : `ruff`, lignes de 100 caractères. Avant de pousser :
  ```bash
  uv run ruff check .
  uv run ruff format .
  uv run pytest
  ```
- **Une seule source de vérité** : chemins et constantes dans `app/config.py`, jamais en dur ailleurs.
- **Chemins calculés depuis `__file__`**, jamais depuis le dossier courant.
- **Secrets** dans des variables d'environnement (`.env` en local, secrets GitHub en CI), jamais dans
  le code. `.env` n'est jamais commité.
- **Dépendances** : uniquement celles qu'on utilise ; les outils de dev vont dans le groupe `dev`.
- **Tests** : chaque fonction et chaque endpoint ont leurs tests, cas d'erreur compris, rangés en
  deux familles :

  | Dossier             | Ce qui est testé                                   | Organisation                     |
  |---------------------|----------------------------------------------------|----------------------------------|
  | `tests/unit/`       | une fonction à la fois, sans HTTP                  | même arborescence que `app/`     |
  | `tests/functional/` | l'API à travers HTTP, comme un vrai client         | un fichier par endpoint          |

  Les fixtures partagées sont dans `tests/conftest.py`. Une suite se lance seule :
  `uv run pytest tests/unit` (rapide, pendant le développement) ou `uv run pytest tests/functional`.
- **Commentaires** en français, pour expliquer le pourquoi, pas le quoi.

## Expérimentation ML

- **Données sources intouchables** : `data/raw/` n'est jamais modifié ; toute transformation est dans
  le code.
- **Reproductibilité** : graine aléatoire fixée dans `app/config.py`, versions des bibliothèques
  figées par `uv.lock`. Deux entraînements identiques donnent le même modèle.
- **Entraînement par script uniquement** : le modèle servi par l'API doit pouvoir être régénéré par
  une seule commande, sans notebook.
- **Le preprocessing fait partie du modèle** : il est sauvegardé avec lui (pipeline scikit-learn),
  pour que l'API applique exactement les transformations de l'entraînement.
- **Métriques mesurées sur un jeu de test** jamais vu pendant l'entraînement, et enregistrées avec le
  modèle.
