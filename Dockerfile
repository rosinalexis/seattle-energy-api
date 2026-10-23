# Image de l'API : Python 3.12 minimal, dépendances figées par uv.lock, modèle entraîné au build.
FROM python:3.12-slim

# uv copié depuis son image officielle, à version fixée (même version qu'en local).
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /bin/uv

WORKDIR /app

# Dépendances d'abord : tant que pyproject.toml et uv.lock ne changent pas, Docker réutilise
# cette couche en cache et ne réinstalle rien quand seul le code change.
COPY pyproject.toml uv.lock ./
# --no-dev : ni pytest ni ruff en production.
RUN uv sync --locked --no-dev

COPY app ./app
COPY scripts ./scripts
COPY data ./data

# Le modèle est entraîné dans l'image : il est reproductible, et l'image livrée contient
# exactement le modèle testé par la CI.
RUN .venv/bin/python -m scripts.train_model

# L'API ne tourne pas en root : si elle était compromise, l'attaquant n'aurait pas les
# droits d'administration du conteneur.
RUN useradd --create-home api
USER api

EXPOSE 8000

# Docker interroge /health régulièrement et marque le conteneur « unhealthy » s'il ne répond plus.
# Pas de curl dans l'image slim : Python fait la requête.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD .venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 0.0.0.0 : écoute sur toutes les interfaces, sinon l'API serait injoignable hors du conteneur.
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
