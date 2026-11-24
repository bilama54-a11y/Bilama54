# Bilama54
Parieur sportif

## Apps en ligne (Android / PWA)

**https://bilama54-a11y.github.io/Bilama54/ucl/** — **UCL Over/Under 2026-27** 🏆
League Phase (36 clubs, 8 journées) : tiers 50/30/20 = 18/11/7, zones de qualification C1,
score global −4 à +4, projection de buts (ligne adaptative 2,5 / 3,5 / 4,5 / auto) et `Journal_Paris`.
Installable sur Android, fonctionne hors-ligne. Doc : [`docs/ucl-over-under.md`](docs/ucl-over-under.md)

**https://bilama54-a11y.github.io/Bilama54/** — **PL Over/Under 2026-27**
20 clubs de Premier League : tiers 10/6/4, analyseur Dom vs Ext, verdict couleur + projection vs
ligne/cote, `Journal_Paris`. Doc : [`docs/pl-over-under.md`](docs/pl-over-under.md)

Les deux apps sont indépendantes (icônes, journaux et caches séparés) et **mettent à jour leurs
statistiques automatiquement** dès que le téléphone retrouve Internet.

## Outils

- **[`ucl/index.html`](ucl/index.html)** — **UCL Over/Under 2026-27** (déployé sur `/ucl/`) :
  36 clubs de la League Phase, tiers 18/11/7, analyseur Dom vs Ext, verdict couleur + projection
  vs ligne/cote, `Journal_Paris` (ROI, winrate, export CSV/JSON), matchs à venir par journée (J5→J8).
- **[`pl/index.html`](pl/index.html)** — **PL Over/Under 2026-27** (déployé à la racine du site) :
  classements & tiers (50/30/20), analyseur Dom vs Ext, verdict couleur, `Journal_Paris`.
- **[`index.html`](index.html)** — PPG Lab (NBA) : calculateur de PPG (global / domicile / extérieur / last 5-6-10), heatmap 5 couleurs et filtre « PPG + cote ». Doc : [`docs/ppg-lab.md`](docs/ppg-lab.md)
- [`analyses/`](analyses) — analyses ponctuelles produites depuis FootyStats.

## Automatisation des données

| Compétition | Collecteur | Workflow | Fréquence | Source |
|---|---|---|---|---|
| Premier League (20 clubs) | [`scripts/update_pl_data.py`](scripts/update_pl_data.py) | [`update-pl-data.yml`](.github/workflows/update-pl-data.yml) | toutes les 6 h | Fantasy Premier League (splits exacts), secours ESPN |
| Champions League (36 clubs) | [`scripts/update_ucl_data.py`](scripts/update_ucl_data.py) | [`update-ucl-data.yml`](.github/workflows/update-ucl-data.yml) | toutes les 6 h | ESPN (résultats agrégés match par match) |

Chaque exécution valide le JSON (nombre de clubs, `mp = dom + ext`, `ΣGF = ΣGA`), commite sur `main`
puis publie la PWA et les données sur `gh-pages` (racine pour la PL, `/ucl/` pour la C1). Les deux
workflows partagent le groupe de concurrence `gh-pages-deploy` : ils ne publient jamais en même temps.

> Le site publié conserve l'ancien dashboard NBA sous `/dashboard-nba.html` et l'app foot 20 ligues sous `/foot.html`.
