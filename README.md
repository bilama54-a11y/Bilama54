# Bilama54
Parieur sportif

## App en ligne (Android / PWA)

**https://bilama54-a11y.github.io/Bilama54/** — **PL Over/Under 2026-27**
Modèle de tiers offensifs/défensifs Premier League, score global −4 à +4, projection de buts,
journal de paris et **mise à jour automatique des statistiques** dès que le téléphone est connecté.
Installable sur Android (Chrome ⋮ → « Installer l'application »), utilisable hors-ligne avec le dernier instantané.

- Doc complète : [`docs/pl-over-under.md`](docs/pl-over-under.md)
- Source de l'app : [`pl/index.html`](pl/index.html) · [`pl/sw.js`](pl/sw.js) · [`pl/manifest.webmanifest`](pl/manifest.webmanifest)
- Données : [`data/pl-2026-27.json`](data/pl-2026-27.json) — rafraîchi par [`scripts/update_pl_data.py`](scripts/update_pl_data.py)
  via GitHub Actions ([`update-pl-data.yml`](.github/workflows/update-pl-data.yml)) toutes les 6 h.

## Outils

- **[`pl/index.html`](pl/index.html)** — **PL Over/Under 2026-27** (déployé à la racine du site) :
  classements & tiers (50/30/20), analyseur Dom vs Ext, verdict couleur + projection vs ligne/cote, `Journal_Paris` (ROI, winrate, export CSV/JSON), synchronisation auto FPL + ESPN.
- **[`index.html`](index.html)** — PPG Lab (NBA) : calculateur de PPG (global / domicile / extérieur / last 5-6-10), heatmap 5 couleurs et filtre « PPG + cote ». Doc : [`docs/ppg-lab.md`](docs/ppg-lab.md)
- [`analyses/`](analyses) — analyses ponctuelles produites depuis FootyStats.

> Sur le site publié, l'ancien dashboard NBA reste accessible via `/dashboard-nba.html` et l'app foot 20 ligues via `/foot.html`.
