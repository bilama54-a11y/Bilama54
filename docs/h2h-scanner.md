# H2H Scanner 2026-27 — registre « victoire sèche » & « Over 1.5 »

App Android (PWA) qui applique deux règles de paris fondées sur le **face-à-face** et les **cotes 1X2**,
avec les cotes publiées par **FootyStats** et un journal de paris intégré.

- **URL** : https://bilama54-a11y.github.io/Bilama54/h2h/
- **Fichiers** : `h2h/index.html`, `h2h/sw.js`, `h2h/manifest.webmanifest`, `h2h/icon*`
- **Données** : `data/h2h-odds.json` (produit par `scripts/update_h2h_odds.py`)
- **Workflow** : `.github/workflows/update-h2h-data.yml` (cron `30 */6 * * *`)

---

## 1. Les règles

### R1 — Victoire sèche

```
taux_H2H(équipe) = victoires / confrontations        (nuls comptés par défaut)
p_book(équipe)   = 1 / cote                          (ou 1/cote normalisée sans marge)

si taux_H2H ≥ 50 %  ET  (p_book − taux_H2H) ≥ 10 points  →  pari 1X2 sur cette équipe
```

Le seuil « +10 » peut passer en **relatif** (× 1,10) dans les réglages : la condition devient
`p_book ≥ taux_H2H × 1,10`.

### R2 — Over 1.5 (favori à l'extérieur)

```
si le favori joue à l'extérieur  ET  50 % < p_book < 60 %   →  Over 1.5
```

`50 % – 60 %` correspond à une cote comprise entre **1,67 et 2,00**.
Par défaut, l'Over 1.5 **remplace** la victoire sèche (réglage « en plus » disponible).

### Réglages disponibles dans l'app

| Réglage | Défaut | Effet |
|---|---|---|
| Nuls comptés dans le taux H2H | ✅ | sinon victoires / (victoires + défaites) |
| Probabilité sans marge | ❌ | normalise 1/cote sur les 3 issues |
| Seuil +10 % relatif | ❌ | sinon écart absolu de 10 points |
| Over 1.5 en plus | ❌ | sinon il remplace le pari simple du favori extérieur |

---

## 2. L'app en 3 onglets

1. **Signaux** — liste des matchs cotés avec, pour chacun : date, H2H détaillé (`W-D-W`, taux des
   deux équipes), cotes 1X2 + Over 1.5, probabilités du book, favori et verdict
   (`✔ 1 Arsenal @ 1,28`, `Over 1.5 @ 1,28`, ou `Aucun pari` + motif).
   Filtres : **Tous / Value / Over 1.5**. Un tap pré-remplit le calculateur.
2. **Calcul** — saisie manuelle (H2H victoires/nuls/défaites + cotes) pour tout match absent de l'API :
   détail des écarts (H2H, probabilité, value en points), verdict et enregistrement au journal.
3. **Journal** — paris avec règle, cote, H2H, value, mise ; règlement Gagné/Perdu/Push, **winrate**,
   **ROI**, profit, export **CSV/JSON**.

---

## 3. Automatisation (FootyStats)

`scripts/update_h2h_odds.py` :

1. `/league-list` → découvre `league_id` / `season_id` de la Premier League (surchargeable par
   `FOOTYSTATS_LEAGUE_ID` / `FOOTYSTATS_SEASON_ID`).
2. `/league-matches?status=incomplete` → prochains matchs (max 24, au-delà d'une heure du coup d'envoi).
3. `/match?match_id=` → `odds_ft_1 / x / 2`, `odds_ft_over15` et le bloc
   `h2h.previous_matches_results` (`team_a_wins`, `team_b_wins`, `draw`, `totalMatches`).
4. Écrit `data/h2h-odds.json`, commité sur `main` puis publié sur `gh-pages` avec l'app.

Sans secret **`FOOTYSTATS_API_KEY`**, le script sort proprement (code 0) : l'app reste utilisable via
le calculateur manuel. Pour l'activer : *Settings → Secrets and variables → Actions → New repository
secret* → nom `FOOTYSTATS_API_KEY` → valeur de la clé FootyStats, puis relancer
« H2H Scanner — cotes FootyStats + publication PWA ».

> Les cotes FootyStats sont des cotes agrégées de bookmakers ; `odds_comparison` contient le détail par
> opérateur si tu veux un jour choisir une enseigne précise.

---

## 4. Installation Android

1. Ouvrir **https://bilama54-a11y.github.io/Bilama54/h2h/** dans Chrome.
2. **⋮ → « Installer l'application »** → icône **H2H**.
3. Synchro auto à l'ouverture, au retour au premier plan, sur retour d'Internet, toutes les 10 min et
   via le bouton **Sync** ; le service worker garde les dernières cotes hors-ligne.

---

## 5. Maintenance

```bash
FOOTYSTATS_API_KEY=xxx python3 scripts/update_h2h_odds.py   # régénère data/h2h-odds.json
python3 -m http.server 8000                                 # aperçu : /h2h/
```

- Changer les seuils : `CFG_DEFAULT` dans `h2h/index.html` (`threshold`, `minH2H`).
- Tester sans clé : `FOOTYSTATS_API_BASE=http://127.0.0.1:8765` permet de pointer sur un mock local.
- Ajouter une autre compétition : dupliquer l'entrée de ligue dans le script (le fichier JSON est
  structuré pour accueillir un tableau `matches` toutes compétitions).
