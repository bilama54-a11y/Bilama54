# La formule : analyser un match avec les xG et les xGA

Formule complète issue de l'étude [`RAPPORT_xG_vs_xGA.md`](RAPPORT_xG_vs_xGA.md), implémentée
dans `modele_xg.py` (bibliothèque standard Python, aucune dépendance), validée par backtest.

---

## 0. Les constantes (toutes mesurées sur 172 équipes-saisons du Big-5)

| Symbole | Valeur | Origine |
|---|---|---|
| `μ` | moyenne de la ligue (≈ **1,55** xG/match/équipe) | à recalculer par ligue |
| `k` | **0,915** | buts réels par xG (mesuré : 0,869 – 0,961) |
| `hfa` | **1,12** | avantage domicile (effet multiplicatif : ×1,12 / ÷1,12) |
| `w_att` | **0,78** sur 38 matchs | fiabilité des xG créés (autocorrélation S1→S2) |
| `w_def` | **0,53** sur 38 matchs | fiabilité des xG concédés (autocorrélation S1→S2) |
| `ρ` (Dixon-Coles) | **0** (option : −0,04) | calibré sur le taux de nuls observé |

---

## 1. La formule en 4 étapes

### Étape 1 — Ratings (avec shrinkage obligatoire)

Pour chaque équipe, sur une fenêtre de **n** matchs :

```
A = (xG90  / μ) ^ w_att        force d'attaque   (1,00 = moyenne de la ligue)
D = (xGA90 / μ) ^ w_def        faiblesse défensive (1,00 = moyenne)
```

**Les exposants sont le cœur de la formule** : ce sont les fiabilités mesurées. Ils
ramènent chaque signal vers la moyenne à hauteur de son bruit. Ils dépendent de la
taille de la fenêtre (généralisation de Spearman-Brown) :

```
w(n) = (r · n) / (r · n + 38)     avec  r = ρ₃₈ / (1 − ρ₃₈)
       r_att = 0,78/0,22 = 3,55      r_def = 0,53/0,47 = 1,13
```

| Fenêtre n | poids attaque | poids défense |
|---|---|---|
| 5 matchs | 0,32 | **0,13** |
| 8 matchs | 0,43 | 0,19 |
| 10 matchs | 0,49 | 0,23 |
| 15 matchs | 0,59 | 0,30 |
| 19 matchs | 0,64 | 0,36 |
| **38 matchs** | **0,78** | **0,53** |
| 76 matchs | 0,88 | 0,69 |

> Sur 5 matchs, une « défense de fer » ne vaut que 13 % de poids : **c'est du bruit à 87 %**.
> C'est la traduction directe du résultat de l'étude (xGA deux fois moins persistant que xG).

**Recommandé :** fenêtre de **10 à 15 matchs** avec une pondération temporelle
demi-vie ≈ 8-10 matchs (le match d'il y a 10 matchs pèse moitié). Puis renormaliser
A et D pour que leur moyenne de ligue vaille 1 (corrige les calendriers asymétriques).

### Étape 2 — Lambdas du match

```
λ_dom = k · μ · A_dom · D_ext · 1,12
λ_ext = k · μ · A_ext · D_dom / 1,12
```

Exemple : domicile à 1,76 – 1,20 → le modèle attend 2,96 buts.

### Étape 3 — Grille de Poisson (scores 0-0 à 12-12)

```
P(i,j) = Poisson(λ_dom, i) · Poisson(λ_ext, j)          [× correction Dixon-Coles si ρ ≠ 0]
P(1) = Σ P(i,j) pour i>j     P(X) = Σ P(i,i)     P(2) = Σ P(i,j) pour i<j
P(1X) = P(1) + P(X)          P(Over 2,5) = Σ P(i,j) pour i+j > 2
P(BTTS) = 1 − P(dom 0) − P(ext 0) + P(0,0)
```

### Étape 4 — Cote juste, edge, mise

```
cote juste = 1 / p
edge       = p · cote_bookmaker − 1
mise       = Kelly/4 = 0,25 · (p·(cote−1) − (1−p)) / (cote−1)
```

---

## 2. Version « de poche » (calculable sans ordinateur)

Soient les écarts **relatifs** à la moyenne de la ligue :
`a = xG90/μ − 1` (attaque) et `d = xGA90/μ − 1` (défense).

```
λ_dom − λ_ext  =  0,32  +  1,42 · [ 0,78·(a_dom − a_ext) + 0,53·(d_ext − d_dom) ]
                   ↑           ↑         ↑                    ↑
                domicile   k·μ = 1,42   poids attaque      poids défense
```

puis lire les probabilités dans la table ci-dessous (total de buts ≈ 2,85) :

| d = λ_dom − λ_ext | P(1) | P(X) | P(2) | P(1X) | P(BTTS) | cote 1 |
|---|---|---|---|---|---|---|
| −1,2 | 0,143 | 0,203 | 0,653 | 0,347 | 0,488 | 6,97 |
| −0,8 | 0,210 | 0,228 | 0,561 | 0,439 | 0,538 | 4,75 |
| −0,4 | 0,288 | 0,245 | 0,467 | 0,533 | 0,567 | 3,47 |
| **0,0** | 0,375 | 0,250 | 0,375 | 0,625 | 0,577 | 2,67 |
| +0,4 | 0,467 | 0,245 | 0,288 | 0,712 | 0,567 | 2,14 |
| +0,8 | 0,561 | 0,228 | 0,210 | 0,790 | 0,538 | 1,78 |
| +1,2 | 0,653 | 0,203 | 0,143 | 0,857 | 0,488 | 1,53 |

**Approximations** (|d| ≤ 1) : `P(1) ≈ 0,380 + 0,223·d` et `P(X) ≈ 0,249 − 0,031·d²`

**Marché des buts** — le total ne dépend QUE de `λ_dom + λ_ext` (pas de l'écart) :

| Total λ | P(Over 1,5) | P(Over 2,5) | P(Over 3,5) |
|---|---|---|---|
| 2,30 | 0,669 | 0,404 | 0,201 |
| 2,70 | 0,751 | 0,506 | 0,286 |
| 2,85 | 0,777 | 0,542 | 0,319 |
| 3,30 | 0,841 | 0,641 | 0,420 |

**Exemple de poche :** équipe à domicile avec +20 % d'attaque et −10 % de xG concédés,
face à un adversaire moyen → d = 0,32 + 1,42·[0,78·0,20 + 0,53·0,10] = **0,62**
→ P(1) ≈ 0,52 · P(X) ≈ 0,24 · P(2) ≈ 0,245 → cotes justes **1,93 / 4,22 / 4,09**.

---

## 3. Validation : backtest 2024/25 → 2025/26

65 équipes présentes dans les deux saisons (EPL, Liga, Bundesliga, Ligue 1).
Ratings construits **uniquement** sur 2024/25 ; aucune donnée du futur.

| Modèle | RMSE brut | RMSE recalé | corr. points réels | corr. points attendus |
|---|---|---|---|---|
| **M0** points de la saison passée (naïf) | **0,327** | 0,3128 | 0,705 | 0,750 |
| M1 xG + xGA sans shrinkage (1,00 / 1,00) | 0,3439 | 0,3009 | 0,731 | 0,776 |
| **M2 formule proposée, plug-in (0,78 / 0,53)** | 0,3496 | 0,2980 | **0,737** | **0,787** |
| M3 attaque seule (0,78 / 0,00) | 0,3667 | 0,3025 | 0,728 | 0,788 |
| M4 défense seule (0,00 / 0,53) | 0,4327 | 0,3623 | 0,570 | 0,584 |
| M5 shrinkage identique (0,65 / 0,65) | 0,3551 | 0,3007 | 0,731 | 0,778 |
| M6 xGD seul (une dimension) | 0,3485 | 0,3015 | 0,730 | 0,770 |
| **M7 formule + moyenne postérieure** | 0,3478 | **0,2971** | **0,739** | 0,785 |

**Comment lire ce tableau (important) :**

* **L'information** (corrélation, RMSE après recalage affine) : la formule **bat nettement**
  la référence naïve « points de la saison passée » : corr **0,739 vs 0,705**, RMSE recalé
  **0,2971 vs 0,3128** (soit **−5,0 %** d'erreur). Sur la cible la plus propre (les points
  attendus xPTS) : **0,787 vs 0,750**.
* **Le RMSE brut** favorise le naïf (0,327) pour une raison mécanique : les points réels
  = points attendus + chance, donc leur dispersion est **plus large** que celle du modèle.
  Ce n'est pas un défaut du modèle : pour estimer des **probabilités de match**, c'est
  exactement l'espérance qu'il faut. Ne « gonflez » donc pas les prédictions.
* **Le shrinkage sert** : sans lui (M1) on perd en corrélation ET le taux de nuls prédits
  tombe à 23,2 % contre **24,0 %** avec shrinkage (observé : **24,8 %**).
* **La défense seule est le plus mauvais modèle** (corr 0,570) — cohérent avec l'étude :
  c'est le signal le plus bruité. L'attaque seule (0,728) fait presque aussi bien que
  les deux réunis (0,737).
* **Les poids sont-ils optimaux ?** Grille de sensibilité (corrélation) :

| w_att \ w_def | 0,00 | 0,25 | 0,50 | 0,75 | 1,00 |
|---|---|---|---|---|---|
| 0,40 | 0,723 | 0,736 | 0,725 | 0,710 | 0,696 |
| 0,60 | 0,726 | 0,738 | 0,735 | 0,726 | 0,715 |
| **0,78** | 0,728 | 0,738 | **0,738** | 0,732 | 0,725 |
| 1,00 | 0,728 | 0,737 | 0,738 | 0,736 | 0,731 |
| 1,20 | 0,728 | 0,736 | 0,738 | 0,737 | 0,734 |

  Optimum de la grille : w_att = 1,00 / w_def = 0,50 (0,738). Les valeurs tirées de
  l'étude (0,78 / 0,53) donnent **0,738** : elles sont **sur le plateau optimal**.
  La surface est très plate → ne sur-optimisez pas ces deux chiffres.

---

## 4. Calibration : le modèle reproduit-il les nuls ?

| | Taux de nuls prédit |
|---|---|
| Observé (3 124 matchs) | **24,8 %** |
| Modèle sans shrinkage | 23,2 % |
| **Modèle avec shrinkage (0,78 / 0,53), ρ = 0** | **24,0 %** |
| Modèle + Dixon-Coles ρ = −0,04 | 24,8 % |

→ Le shrinkage fait presque tout le travail. On peut donc garder **ρ = 0** (Poisson
indépendant) ; si l'on veut coller exactement au taux de nuls, **ρ = −0,04**.

---

## 5. Exemple complet (ratings 2025/26, shrinkage 0,78 / 0,53)

**Arsenal – Manchester City** ( Emirates) : λ = **1,76 – 1,20** (total 2,95)

| Marché | Probabilité | Cote juste | Cote bookmaker | Edge | Kelly/4 |
|---|---|---|---|---|---|
| Arsenal | 50,6 % | 1,98 | 2,10 | **+6,2 %** | 1,42 % |
| Nul | 23,5 % | 4,26 | 3,60 | −15,5 % | — |
| Man City | 25,9 % | 3,85 | 3,40 | −11,8 % | — |
| Arsenal ou nul (1X) | 74,1 % | 1,35 | 1,35 | 0,0 % | — |
| Over 2,5 | 56,6 % | 1,77 | 1,75 | −0,9 % | — |
| BTTS | 57,7 % | 1,73 | — | — | — |
| Clean sheet Arsenal | 30,3 % | 3,30 | — | — | — |

Autres exemples (cotes justes) :

| Match | λ | 1 / X / 2 |
|---|---|---|
| Real Madrid – Barcelone | 1,93 – 1,69 | **2,28 / 4,60 / 2,91** |
| Bayern – Dortmund | 2,38 – 1,39 | **1,68 / 5,24 / 4,66** |
| Inter – Juventus | 1,74 – 1,22 | **2,02 / 4,24 / 3,73** |
| PSG – Marseille | 2,06 – 1,27 | **1,80 / 4,73 / 4,32** |

---

## 6. Règles de décision

1. **Jouer si edge ≥ 3 à 5 %.** En dessous, l'incertitude du modèle (et de vos données
   xG) dépasse l'avantage. Le backtest donne un écart-type résiduel d'environ
   **0,30 point/match** : c'est l'ordre de grandeur du bruit à ne pas confondre avec un edge.
2. **Mise = Kelly / 4** (ou /5) : la formule estime des probabilités, pas des certitudes.
3. **Marchés à privilégier** selon l'étude :
   * *Victoire / handicap* → l'attaque porte le signal (pondération ≈ 1,5 : 1).
   * *1X / X2 / « ne pas perdre »* → la défense redevient aussi importante (≈ 1 : 1) :
     n'hésitez pas à jouer les équipes au profil défensif sur ces marchés (à xGD égal,
     elles font +2,8 points de « ne pas perdre »).
   * *Over/Under* → ne dépend que de `λ_dom + λ_ext`, donc de l'attaque des deux et de la
     défense des deux, à parts égales.
4. **Ne jamais sur-réagir à une série défensive courte** (cf. table des poids).
5. **Comparez systématiquement à la cote de clôture** : si votre edge disparaît en
   fin de marché, c'est que l'information était déjà dans le prix.

---

## 7. Limites et prochaines étapes

* **Données agrégées** : le backtest est au niveau saison (pas match par match). La
  validation idéale — log-loss et calibration par tranche de cote sur des milliers de
  matchs — demande des xG **match par match** (Understat/FBref). C'est l'étape suivante
  naturelle et je peux la faire si vous fournissez un export.
* **BTTS / score exact** : le Poisson indépendant surestime probablement les BTTS
  (57,7 % sur un match équilibré, contre ~52 % dans la réalité du Big-5). Le correctif est
  une **surdispersion** (Poisson à λ aléatoire / binomiale négative), non calibrable sans
  données de match. À réserver ou à recaler sur le marché.
* **Pas d'ajustement d'adversaire** dans la version simple. Rafinement possible (1 itération) :
  `A_i ← xG_i / (moyenne des D des adversaires rencontrés)`, puis renormaliser.
* **Non pris en compte** : blessures, compositions, calendrier, météo, état du terrain,
  et le fait qu'une partie du xG dépend du scénario du match (game state).
* **Le marché reste la référence** : un modèle xG seul bat rarement la cote de clôture.
  L'intérêt est de repérer les désaccords ≥ 5 % et de les confronter à l'information
  qualitative (absents, enjeu, voyage).

---

## 8. Utiliser le code

```bash
python3 modele_xg.py              # tout : backtest, calibration, tables, exemples
python3 modele_xg.py backtest     # validation uniquement
python3 modele_xg.py calibrer     # calibrage de rho sur le taux de nuls
python3 modele_xg.py table        # table de lecture + marchés de buts
```

API : `ratings()`, `fiabilite(n, rho)`, `lambdas()`, `probas()`, `buts()`,
`cote_juste()`, `value()`, `kelly()` — importables depuis `modele_xg.py`.
