# Foot — Activer le live FootyStats (20 ligues)

`foot.html` est déjà câblé pour charger `data/ppg_live.json` au démarrage + toutes les 60s (`Auto 60s`).  
Le GitHub Action `.github/workflows/fetch-ppg.yml` remplit ce fichier tous les jours à **06:00 UTC** (07:00 Paris) + à la demande.

## Mode actuel : démo
- Sans clé, la dashboard utilise la clé `example` (limitée à PL 2018/19) + le fallback **Coller PPG**.
- `data/ppg_live.json` contient `note: Mode démo...` → la banner affiche l'heure de dernière sync + `utilise Coller PPG`.

## Passer en vrai live (toutes les 20 ligues 2026-27)

1. Va sur https://footystats.org/api
2. Abonne-toi (à partir de **£29.99 / mois** — accès `api.football-data-api.com`).
3. Copie ta clé sur https://footystats.org/api/u/api-settings → section **API Key**.
4. Dans ce repo GitHub : **Settings → Secrets and variables → Actions → New repository secret**
   - **Name:** `FOOTYSTATS_API_KEY`
   - **Value:** colle ta clé (ex: `abc123...`)
   - Save.
5. Va dans **Actions → Fetch FootyStats PPG Live → Run workflow** (bouton à droite).
   - Le workflow va appeler `https://api.football-data-api.com/league-tables?key=TA_CLE&season_id=...&include=stats`
   - Parser `seasonPPG_home / _away / _overall` pour chaque équipe des 20 ligues.
   - Écrire `data/ppg_live.json` + commit sur `gh-pages`.
6. Recharge `foot.html` → la banner passe à `✅ 312 PPG live • 20/10/2026 08:12 • source FootyStats API` et tous les signaux `WIN ≤1.5 / DOUBLE >1.5 / PASS` sont recalculés avec les vrais PPG domicile/extérieur.

## Que fait la dashboard quand la clé est là ?

```js
// au load
loadLivePPG() // fetch('data/ppg_live.json') → écrase fullTeams[lid] → render() + picker
scheduleAutoRefresh() // toutes les 60s : sauve localStorage + refetch silencieux
// manuel
fetchFootyStatsLive() // bouton 🔄 — tente corsproxy.io direct + fallback Coller PPG
applyPastePPG() // colle "Equipe 1.23" → écrase fullTeams[lid] + localStorage
```

## Sans abonnement ? Alternative gratuite

- Utilise le **bouton Coller PPG** : ouvre https://footystats.org/france/ligue-1 etc. → copie la colonne **PPG** (ou **Home PPG / Away PPG**) → choisis la ligue dans le menu → colle → **Appliquer**.  
- Sauvé en `localStorage` → persiste entre recharges.

## Coûts / quotas

- FootyStats facture le nombre de ligues sélectionnées (changeable chaque mois dans les settings API).
- Le workflow met `sleep 0.6s` entre chaque ligue pour respecter le rate-limit.

Besoin d'aide ? Ouvre une issue avec ta clé masquée (`***abcd`) + log de l'Action.
