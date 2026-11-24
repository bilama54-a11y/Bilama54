# UCL Over/Under 2026-27 — mode d'emploi

Version Ligue des Champions du modèle Over/Under « tiers » : les **36 clubs de la League Phase**
sont classés par rythme offensif et défensif, puis un score global de `−4` à `+4` décide du verdict.

- **URL** : https://bilama54-a11y.github.io/Bilama54/ucl/
- **App** : `ucl/index.html` · `ucl/manifest.webmanifest` · `ucl/sw.js`
- **Données** : `data/ucl-2026-27.json` (36 clubs, J4) · **collecteur** : `scripts/update_ucl_data.py`
- **Automatisation** : `.github/workflows/update-ucl-data.yml` (toutes les 6 h + à la demande)
- Version Premier League (20 clubs) : https://bilama54-a11y.github.io/Bilama54/

---

## 1. Le format qui change tout

La League Phase 2026-27 compte **36 clubs** et **8 matchs par club** (4 à domicile, 4 à l'extérieur),
contre des adversaires tous différents. Conséquences pour le modèle :

| Premier League (20 clubs) | Champions League (36 clubs) |
|---|---|
| 34-38 matchs par club | **8 matchs** par club |
| 50 / 30 / 20 % = **10 / 6 / 4** | 50 / 30 / 20 % = **18 / 11 / 7** |
| moyennes très stables | moyennes **très volatiles** (1 à 4 matchs par côté) |

L'app affiche donc systématiquement **l'échantillon** (`m dom.` / `m ext.`) sur chaque brique et
signale le mode global comme plus fiable tant que les splits ne sont pas mûrs.

---

## 2. Le modèle

### Tiers (calculés sur des moyennes par match, jamais sur des totaux)

| Rang | Tier | Attaque (BM/m) | Défense (BE/m, #1 = meilleure) |
|---|---|---|---|
| `#1 – #18` | Tier 1 | **+1** (OVER) | **−1** (UNDER) |
| `#19 – #29` | Tier 2 | **0** | **0** |
| `#30 – #36` | Tier 3 | **−1** (UNDER) | **+1** (OVER) |

Les bornes sont génériques (`50 %` puis `30 %` de l'effectif) : le même code produit `10 / 6 / 4`
pour 20 clubs et `18 / 11 / 7` pour 36.

### Score global

```
Score = Off_Dom + Déf_Dom + Off_Ext + Déf_Ext     (−4 … +4)
```

| Score | Couleur | Verdict |
|---|---|---|
| `+2 … +4` | 🔴 | **OVER [ligne] FORT** — 2 unités |
| `+1` | 🟠 | **OVER [ligne] LÉGER** — 1 unité max |
| `0` | 🟡 | **NEUTRE** — No Bet |
| `−1` | 🔵 clair | **UNDER [ligne] LÉGER** — 1 unité max |
| `−2 … −4` | 🔵 | **UNDER [ligne] FORT** — 2 unités |

Le libellé reprend la ligne choisie (`3,5` par défaut en C1).

### Ligne par défaut : 3,5 et non 2,5

La League Phase 2026-27 tourne à **≈ 4,0 buts/match** (291 buts en 72 matchs après la J4) :
une ligne à 2,5 serait mécaniquement « OVER ». L'app propose donc :

- **2,5 / 3,5 / 4,5** en un tap,
- **Auto** : ligne arrondie au demi-point le plus proche de la moyenne C1 courante (ici `4,0`).

### Projection de buts

```
Projection = ((BM_Dom + BE_Ext) + (BM_Ext + BE_Dom)) / 2
```

- **Mode Global** : moyennes globales (recommandé en C1 avec 8 matchs).
- **Mode Split Dom/Ext** : 4 matchs à domicile / 4 à l'extérieur (précis mais fragile).
- Le total est modélisé par une loi de **Poisson** → `P(OVER)`, `P implicite = 1/cote`,
  `edge = P × cote − 1`, mise **Kelly ¼**.

---

## 3. Les 4 étapes de l'app

1. **Classements & Tiers** — les 36 clubs triés par place, avec BM/m, BE/m, rangs, tiers et
   **zones de qualification C1** (1-8 : 8es directs · 9-24 : barrages · 25-36 : éliminés) ;
   bascule Global / Domicile / Extérieur ; matchs à venir **par journée (J5 → J8)**.
2. **Analyseur Dom vs Ext** — les 4 briques avec rang, tier et **nombre de matchs** de l'échantillon.
3. **Score Global & Verdict** — jauge −4 → +4, verdict couleur, projection vs moyenne C1,
   ligne / cote / mise → edge, P(OVER), Kelly.
4. **Journal_Paris** — paris persistants, règlement Gagné/Perdu/Push, **winrate, ROI**, export **CSV/JSON**.

---

## 4. Mise à jour automatique

### GitHub Actions (serveur, toutes les 6 h)

`scripts/update_ucl_data.py` interroge l'API publique **ESPN** (sans clé) :

1. `…/soccer/uefa.champions/standings` → classement officiel, totaux par club ;
2. `…/soccer/uefa.champions/scoreboard?dates=…` (fenêtres de 12 jours sur toute la phase de ligue)
   → **tous les résultats match par match**, agrégés pour reconstruire les **splits Domicile/Extérieur
   exacts** ;
3. les affiches déjà jouées sont retirées du calendrier ; les nouvelles sont ajoutées.

Contrôles bloquants avant publication : 36 clubs, `mp = home.mp + away.mp`, `ΣGF = ΣGA`,
moyenne de buts plausible. Si les splits ne peuvent pas être reconstruits, ils sont estimés et
marqués `splitsEstimated: true`.

Le JSON est commité sur `main` puis **publié sur `gh-pages` dans `/ucl/`** ; GitHub Pages redéploie seul.

### Synchronisation directe sur le téléphone

À l'ouverture, au retour au premier plan, sur l'événement `online`, toutes les 10 min et via le
bouton **Sync** : `./data/ucl-2026-27.json` (puis `../data/…`, puis `raw.githubusercontent.com`) et
**fusion ESPN live** si la compétition a une journée d'avance (garde-fous : ΣGF = ΣGA, 1,2–6 buts/match).
Cache `localStorage` + **instantané embarqué** dans le HTML pour le premier lancement hors-ligne.

Le service worker `ucl/sw.js` est en **network-first** sur les données et les pages : jamais de stats
périmées quand Internet est disponible.

---

## 5. Installation Android

1. Ouvrir **https://bilama54-a11y.github.io/Bilama54/ucl/**
2. Chrome **⋮ → « Installer l'application »**
3. Icône **UCL O/U** (anneau doré, étoiles) à côté de l'icône **PL O/U**.

Les deux apps sont indépendantes : journaux, réglages et caches séparés.

---

## 6. Maintenance

```bash
python3 scripts/update_ucl_data.py     # régénère data/ucl-2026-27.json
python3 -m http.server 8000            # puis http://localhost:8000/ucl/
```

- **Forcer une mise à jour** : Actions → « UCL 2026-27 — stats auto + publication PWA » → *Run workflow*.
- **Saison suivante** : aucune saisie manuelle, le script lit le classement ESPN de la saison en cours
  (vérifier simplement que `WINDOW_START` / `WINDOW_END` couvrent bien la phase de ligue).
- Les deux workflows (PL et UCL) partagent le groupe de concurrence `gh-pages-deploy` : ils ne
  publient jamais en même temps.

---

## 7. Limites connues

- **8 matchs seulement** : un tier peut basculer d'un match à l'autre ; le score 0 doit souvent
  rester un No Bet.
- En split, certains clubs n'ont que **1 ou 2 matchs** d'un côté : l'échantillon est affiché pour
  éviter les fausses certitudes.
- ESPN fournit les totaux officiels ; les splits sont reconstruits depuis les feuilles de match
  (légères différences possibles en cas de match reporté/annulé).
- Poisson suppose l'indépendance des buts : la cote du bookmaker reste l'arbitre final.
