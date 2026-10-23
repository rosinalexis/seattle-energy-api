-- Requêtes d'exemple pour interroger la base.
--
-- Exécution (la base tourne dans docker-compose) :
--   docker compose exec -T db psql -U admin -d seattle_energy < scripts/requetes.sql

-- 1. Les 10 dernières prédictions : ce qui a été envoyé, ce que le modèle a répondu.
SELECT e.id, e.cree_le, e.quartier, e.type_usage, e.surface_batie,
       round(s.consommation_kbtu) AS consommation_predite_kbtu, s.version_modele
FROM prediction_entrees AS e
JOIN prediction_sorties AS s ON s.entree_id = e.id
ORDER BY e.cree_le DESC
LIMIT 10;

-- 2. Tentatives sans réponse du modèle (entrée enregistrée, aucune sortie) : à surveiller.
SELECT e.id, e.cree_le
FROM prediction_entrees AS e
LEFT JOIN prediction_sorties AS s ON s.entree_id = e.id
WHERE s.id IS NULL;

-- 3. Prédictions sur les bâtiments du dataset : écart relatif médian entre prédit et réel.
SELECT count(*) AS predictions,
       round(percentile_cont(0.5) WITHIN GROUP (
           ORDER BY abs(s.consommation_kbtu - b.consommation_reelle_kbtu) / b.consommation_reelle_kbtu
       )::numeric, 3) AS erreur_relative_mediane
FROM prediction_entrees AS e
JOIN prediction_sorties AS s ON s.entree_id = e.id
JOIN batiments AS b ON b.id = e.batiment_id;

-- 4. Volume de prédictions par jour et par version du modèle.
SELECT date_trunc('day', s.cree_le)::date AS jour, s.version_modele, count(*) AS predictions
FROM prediction_sorties AS s
GROUP BY jour, s.version_modele
ORDER BY jour DESC;

-- 5. Le dataset : consommation réelle médiane par type d'usage.
SELECT type_usage, count(*) AS batiments,
       round(percentile_cont(0.5) WITHIN GROUP (ORDER BY consommation_reelle_kbtu)) AS consommation_mediane_kbtu
FROM batiments
GROUP BY type_usage
ORDER BY consommation_mediane_kbtu DESC;
