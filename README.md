# Bilama54
Parieur sportif

## Apps en ligne (Android / PWA)

**https://bilama54-a11y.github.io/Bilama54/ucl/** — **UCL Over/Under 2026-27** 🏆
League Phase (36 clubs, 8 journées) : tiers 50/30/20 = 18/11/7, zones de qualification C1,
score global −4 à +4, projection de buts (ligne adaptative 2,5 / 3,5 / 4,5 / auto) et `Journal_Paris`.
Installable sur Android, fonctionne hors-ligne. Doc : [`docs/ucl-over-under.md`](docs/ucl-over-under.md)

**https://bilama54-a11y.github.io/Bilama54/paliers/** — **PL Paliers 2026-27** 📐 *(nouveau)*
Modèle Over/Under **à seuils absolus** : attaque `≥ 1,40` but/match → `+1` OVER · `1,00–1,39` → `0` ·
`< 1,00` → `−1` ; défense en miroir (`≤ 1,00` → `−1`, `≥ 1,40` → `+1`). Aucun rang, aucun 50/30/20.
Score global −4 à +4, projection vs ligne/cote, `Journal_Paris`. Doc : [`docs/pl-paliers.md`](docs/pl-paliers.md)

**https://bilama54-a11y.github.io/Bilama54/h2h/** — **H2H Scanner 2026-27** 🎯 *(nouveau)*
Registre face-à-face : taux H2H ≥ 50 % + cotes 1X2 FootyStats → **victoire sèche** si la value dépasse
10 points ; **favori à l'extérieur entre 50 % et 60 %** → **Over 1.5**. Signaux automatiques, calculateur
manuel, journal (winrate/ROI). Doc : [`docs/h2h-scanner.md`](docs/h2h-scanner.md)

**https://bilama54-a11y.github.io/Bilama54/** — **PL Over/Under 2026-27**
20 clubs de Premier League : tiers 10/6/4, analyseur Dom vs Ext, verdict couleur + projection vs
ligne/cote, `Journal_Paris`. Doc : [`docs/pl-over-under.md`](docs/pl-over-under.md)

Les apps sont indépendantes (icônes, journaux et caches séparés) et **mettent à jour leurs
statistiques automatiquement** dès que le téléphone retrouve Internet.

## Outils

- **[`h2h/index.html`](h2h/index.html)** — **H2H Scanner** : règles R1 (victoire sèche +10 pts de value
  sur un H2H ≥ 50 %) et R2 (Over 1.5 si le favori extérieur est coté 50-60 %), collecteur FootyStats.
- **[`paliers/index.html`](paliers/index.html)** — **PL Paliers** : modèle à seuils absolus (1,40 / 1,00),
  badges de paliers, mêmes projection/verdict/journal que le modèle par rangs.
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
