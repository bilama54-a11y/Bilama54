# PL Over/Under 2026-27 — mode d'emploi

Application Android (PWA) qui applique le modèle Over/Under « tiers » à la **Premier League 2026-27**
et **met à jour ses statistiques automatiquement** dès que le téléphone a Internet.

- **URL** : https://bilama54-a11y.github.io/Bilama54/
- **Fichiers** : `pl/index.html` (app), `pl/sw.js` (service worker), `pl/manifest.webmanifest` (PWA), `data/pl-2026-27.json` (instantané), `scripts/update_pl_data.py` (collecteur), `.github/workflows/update-pl-data.yml` (planificateur).

---

## 1. Le modèle, en une page

### Données par club (20 clubs)

| Champ | Signification |
|---|---|
| `mp`, `w`, `d`, `l`, `pts` | matchs joués, victoires, nuls, défaites, points |
| `gf`, `ga` | buts marqués / encaissés (total) |
| `home`, `away` | mêmes compteurs **restreints** aux matchs à domicile / à l'extérieur |
| `form` | 5 derniers résultats (`WWDLW`) |

Rythmes utilisés par le modèle :

- **BM/m** = buts marqués par match
- **BE/m** = buts encaissés par match

### Répartition 50 % / 30 % / 20 % (20 clubs → 10 / 6 / 4)

| Rang | Exemple | Points attaque | Points défense |
|---|---|---|---|
| `#1 – #10` | Tier 1 | **+1** (OVER) | **−1** (UNDER) |
| `#11 – #16` | Tier 2 | **0** | **0** |
| `#17 – #20` | Tier 3 | **−1** (UNDER) | **+1** (OVER) |

- Classement **attaque** : BM/m décroissant (`#1` = meilleure attaque).
- Classement **défense** : BE/m croissant (`#1` = meilleure défense).
- Les rangs sont recalculés sur des **moyennes par match** : une équipe avec un match de retard n'est pas pénalisée.

### Score global

```
Score = Off_Dom + Déf_Dom + Off_Ext + Déf_Ext     (de −4 à +4)
```

| Score | Couleur | Verdict |
|---|---|---|
| `+2 … +4` | 🔴 rouge | **OVER 2.5 FORT** — 2 unités |
| `+1` | 🟠 orange | **OVER 2.5 LÉGER** — 1 unité max |
| `0` | 🟡 jaune | **NEUTRE** — No Bet / prudence |
| `−1` | 🔵 bleu clair | **UNDER 2.5 LÉGER** — 1 unité max |
| `−2 … −4` | 🔵 bleu | **UNDER 2.5 FORT** — 2 unités |

### Projection de buts

```
Projection = ((BM_Dom + BE_Ext) + (BM_Ext + BE_Dom)) / 2
```

- **Mode Global** : les quatre valeurs sont les moyennes globales (comportement d'origine).
- **Mode Split Dom/Ext** : `BM_Dom` = buts marqués à domicile par match, `BE_Ext` = buts encaissés à l'extérieur par match, etc. Plus fin, mais sensible aux petits échantillons (5-6 matchs).

### Probabilité & valeur

Le total de buts est modélisé par une loi de **Poisson** de paramètre `Projection` :

- `P(OVER)` = 1 − P(0) − … − P(⌊ligne⌋)
- `P implicite` = 1 / cote
- `Edge` = `P(modèle) × cote − 1` (vert si > 0)
- `Mise conseillée` = Kelly fractionné (¼), plafonné à 25 % de la mise

---

## 2. Les 4 étapes de l'app

1. **Classements & Tiers** — tableau des 20 clubs (J, BM/m, rang, tier, BE/m, rang, tier) avec bascule **Global / Domicile / Extérieur**, moyenne de buts de la ligue, et la liste des **prochains matchs** (1 tap = match chargé).
2. **Analyseur Dom vs Ext** — sélection Domicile / Visiteuse (inversion en un tap) et affichage des **4 briques** avec leur rang et leur tier.
3. **Score Global & Verdict** — jauge −4 → +4, verdict couleur, projection de buts vs moyenne de la ligue, puis **Projection vs Ligne & Cote** (ligne, cote, mise → edge, P(OVER), Kelly) et bouton **Enregistrer au Journal_Paris**.
4. **Journal_Paris** — chaque pari est conservé localement, réglable en Gagné / Perdu / Push, avec **winrate**, **ROI**, profit, export **CSV** (Excel FR) et **JSON**.

---

## 3. Mise à jour automatique (le cœur du système)

Deux couches complémentaires :

### a) GitHub Actions (serveur, toutes les 6 h)

`.github/workflows/update-pl-data.yml` → `scripts/update_pl_data.py` :

1. **API officielle Fantasy Premier League** (`bootstrap-static` + `fixtures`) : source principale, gratuite et sans clé. Recalcul des totaux **et des splits Domicile/Extérieur** à partir de chaque match terminé, plus le calendrier à venir.
2. **Secours ESPN** (`/apis/v2/sports/soccer/eng.1/standings` + `scoreboard`) si la FPL est indisponible ; les splits sont alors conservés/estimés et marqués comme tels.
3. Le JSON est validé (20 équipes, `mp = home.mp + away.mp`, Σbuts marqués = Σbuts encaissés) puis commité sur `main` **et publié sur `gh-pages`** avec l'app. GitHub Pages redéploie automatiquement.

Déclencheurs : `schedule` (cron `15 */6 * * *`), `workflow_dispatch`, et tout `push` touchant `pl/**` ou le script.

### b) Synchronisation directe sur le téléphone

À l'ouverture, au retour au premier plan (`visibilitychange`), sur l'événement `online`, toutes les 10 minutes et via le bouton **Sync** :

1. `fetch` de `./data/pl-2026-27.json` (avec cache-buster), puis `../data/…`, puis `raw.githubusercontent.com/…` en secours.
2. Requête **ESPN** en direct (CORS ouvert) : si ESPN a joué **plus de matchs** que l'instantané, les totaux sont fusionnés et la journée avancée (garde-fou : ΣGF = ΣGA et moyenne 1,5–4,5 buts/match, sinon fusion refusée).
3. Résultat mis en cache dans `localStorage` → **hors-ligne = dernier état connu**, jamais un écran vide (un instantané complet est même embarqué dans le HTML pour le tout premier lancement).

### Service worker (`pl/sw.js`)

- `data/*.json` : **network-first** (jamais de stats périmées quand Internet est là) avec repli cache.
- Navigations : network-first + repli cache.
- Assets : cache-first + rafraîchissement en tâche de fond.

---

## 4. Installation sur Android

1. Ouvrir **https://bilama54-a11y.github.io/Bilama54/** dans Chrome.
2. Menu **⋮ → « Installer l'application »** (ou « Ajouter à l'écran d'accueil »).
3. L'icône **PL O/U** apparaît sur l'écran d'accueil ; l'app s'ouvre en plein écran (standalone) et fonctionne hors-ligne.
4. Vérifier la synchro : le badge en haut à droite passe à **À jour** (vert) ; en cas de coupure il affiche **Hors-ligne**.

> `id`/`scope` du manifeste = `/Bilama54/`. Installer depuis la racine du site garantit le bon périmètre.

---

## 5. Maintenance

```bash
# régénérer l'instantané à la main (nécessite Internet vers fantasy.premierleague.com)
python3 scripts/update_pl_data.py

# vérifier l'app en local
python3 -m http.server 8000        # → http://localhost:8000/pl/
```

- **Changer de saison** : modifier `SEASON` dans le script ; le reste est piloté par les données.
- **Forcer la mise à jour** : onglet *Actions* → « PL 2026-27 — stats auto + publication PWA » → *Run workflow*.
- **Après une fusion de PR sur `main`** : le workflow republie `gh-pages` (l'ancien dashboard NBA est sauvegardé une seule fois sous `/dashboard-nba.html`).
- **Sauvegarde du journal** : bouton CSV/JSON de l'onglet Journal (les données restent sur l'appareil).

---

## 6. Limites connues

- Les splits Dom/Ext dépendent de la FPL ; en secours ESPN ils sont estimés (champ `splitsEstimated`).
- Échantillon de 11 matchs : un tier peut basculer après une seule journée — d'où le verdict « léger » et la prudence à score 0.
- Poisson suppose l'indépendance des buts : la cote du bookmaker reste la référence finale.
- L'API FPL n'envoie pas d'en-tête CORS : elle est **uniquement** appelée côté serveur (Action), jamais depuis le navigateur.
