# PL Paliers 2026-27 — le modèle Over/Under par seuils

Application Android (PWA) qui applique le modèle Over/Under **à seuils absolus** à la Premier League
2026-27, sans aucun classement ni répartition 50/30/20.

- **URL** : https://bilama54-a11y.github.io/Bilama54/paliers/
- **Fichiers** : `paliers/index.html` (app), `paliers/sw.js`, `paliers/manifest.webmanifest`, `paliers/icon*`
- **Données** : `data/pl-2026-27.json` (le même flux FPL/ESPN que l'app PL par rangs, rafraîchi toutes les 6 h)
- **Déploiement** : `.github/workflows/update-pl-data.yml` publie l'app sur `gh-pages` à chaque mise à jour

---

## 1. Les seuils

Aucun rang : chaque équipe est jugée sur ses **moyennes par match**.

### Face offensive — buts marqués (`BM/m`)

| Palier | Condition | Points | Sens |
|---|---|---|---|
| **P1** | `BM/m ≥ 1,40` | **+1** | OVER |
| **P2** | `1,00 ≤ BM/m < 1,40` | **0** | neutre |
| **P3** | `BM/m < 1,00` | **−1** | UNDER |

### Face défensive — buts encaissés (`BE/m`), logique inverse

| Palier | Condition | Points | Sens |
|---|---|---|---|
| **P1** | `BE/m ≤ 1,00` | **−1** | UNDER |
| **P2** | `1,00 < BE/m < 1,40` | **0** | neutre |
| **P3** | `BE/m ≥ 1,40` | **+1** | OVER |

> Les bornes 1,00 et 1,40 encadrent la moyenne réelle du championnat (2,75 buts/match en 2026-27, soit
> 1,375 but par équipe et par match) : au-dessus de 1,40 une attaque est réellement productive, en dessous
> de 1,00 elle est stérile. La zone 1,00–1,39 est volontairement neutre (pas de trou de barème).

### Score global

```
Score = Off_Dom + Déf_Dom + Off_Ext + Déf_Ext     (de −4 à +4)
```

| Score | Verdict |
|---|---|
| `+2 … +4` | 🔴 **OVER 2.5 FORT** (2 unités) |
| `+1` | 🟠 **OVER 2.5 LÉGER** (1 unité) |
| `0` | 🟡 **NEUTRE — No Bet** |
| `−1` | 🔵 **UNDER 2.5 LÉGER** (1 unité) |
| `−2 … −4` | 🔵 **UNDER 2.5 FORT** (2 unités) |

### Projection de buts

```
Projection = ((BM_Dom + BE_Ext) + (BM_Ext + BE_Dom)) / 2
```

Le mode **Global** utilise les moyennes globales ; le mode **Split Dom/Ext** utilise les splits
(4 matchs à domicile / 4 à l'extérieur pour la C1, 5-6 en PL) et applique **les mêmes seuils**.

---

## 2. L'app en 4 étapes

1. **Paliers & Seuils** — tableau des 20 clubs : `J · BM/m · Pal. · BE/m · Pal. · ±` avec badges
   `P1 +1`, `P2 0`, `P3 −1` colorés, tri par performance offensive décroissante, bascule Global /
   Domicile / Extérieur, moyenne de buts du championnat, prochains matchs en 1 tap.
2. **Analyseur Dom vs Ext** — les 4 briques, chacune affichant **la valeur, le palier et le seuil franchi**
   (ex. `1,55 · P1 (≥ 1,40)`).
3. **Score Global & Verdict** — jauge −4 → +4, verdict couleur, projection vs moyenne, puis
   projection vs ligne & cote (P(OVER) Poisson, edge, Kelly ¼).
4. **Journal_Paris** — paris enregistrés localement, règlement Gagné/Perdu/Push, winrate, ROI,
   export CSV (colonne `Modele` = « Seuils 1,40 / 1,00 ») et JSON.

---

## 3. Différences avec le modèle par rangs (`/`)

| | Modèle par rangs | **PL Paliers** |
|---|---|---|
| Découpage | rangs 1-10 / 11-16 / 17-20 (50/30/20) | seuils `1,40` / `1,00` |
| Équipes par palier | fixe (10 / 6 / 4) | variable (7 / 11 / 2 actuellement) |
| Sensible à la concurrence | oui (un rang dépend des autres) | non (valeur intrinsèque) |
| Début de saison | bruit des petits échantillons | plus stable |

Exemple mesuré (J11, mode global) : **Arsenal–Man City** sort `+1 OVER léger` avec les seuils
(1,55 et 2,00 en attaque compensés par 0,64 et 1,27 en défense), là où le modèle par rangs sortait `0`.

> ⚠️ En mode split, les seuils absolus favorisent l'OVER à domicile (moyenne 1,58 but/équipe) et
> l'UNDER à l'extérieur (1,17). Le mode **Global** reste la référence.

---

## 4. Installation Android & synchro

1. Ouvrir **https://bilama54-a11y.github.io/Bilama54/paliers/** dans Chrome.
2. **⋮ → « Installer l'application »** → icône **Paliers** sur l'écran d'accueil (mode standalone).
3. La synchro se fait **automatiquement** : à l'ouverture, au retour au premier plan, sur l'événement
   `online`, toutes les 10 minutes et via le bouton **Sync**.
   - JSON publié (FPL officiel) → `./data/pl-2026-27.json`, puis `../data/…`, puis raw.githubusercontent.
   - Fusion **ESPN live** si elle a une journée d'avance (garde-fous : ΣGF = ΣGA, 1,5–4,5 buts/match).
   - Hors-ligne : dernier instantané en cache + instantané embarqué pour le premier lancement.

---

## 5. Maintenance

```bash
python3 scripts/update_pl_data.py     # régénère data/pl-2026-27.json (FPL → secours ESPN)
python3 -m http.server 8000           # aperçu local : /paliers/
```

- Changer les seuils : constante `SEUILS` en tête du moteur dans `paliers/index.html`
  (`{ off: { p1: 1.40, p2min: 1.00 }, def: { p1: 1.00, p3: 1.40 } }`).
- Les libellés de paliers sont dans `LBL_PALIER` (usage : infobulles du tableau).
- Le workflow `update-pl-data.yml` publie `/paliers/` en même temps que l'app PL à chaque exécution.
