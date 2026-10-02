# xG vs xGA : lequel pèse le plus sur une victoire / sur le fait de ne pas perdre ?

**Étude chiffrée sur le Big-5 (Premier League, La Liga, Bundesliga, Serie A, Ligue 1), saisons 2024/25 et 2025/26.**
Données : Understat — 172 équipes-saisons, 9 ligues-saisons.
Code : `analyse_xg_xga.py` · Données : `data/understat_team_seasons.csv` · Sortie brute : `resultats_xg_xga.txt`

---

## 1. La réponse en 4 lignes

1. **Pour GAGNER, c'est l'attaque (xG) qui pèse le plus.** +0,1 xG/90 créé vaut **+2,4 points** de probabilité de victoire, contre **+2,0 points** pour 0,1 xGA/90 concédé en moins (terrain neutre). En écart-type réel (l'amplitude des écarts entre équipes d'une même ligue) : **+8,7 pts de P(victoire) pour l'attaque contre +5,3 pts pour la défense**.
2. **Pour NE PAS PERDRE, la défense reprend l'avantage.** 0,1 xGA/90 en moins vaut **+2,5 pts** de probabilité de « ne pas perdre », contre **+2,0 pts** pour 0,1 xG/90 en plus. En écart-type réel : **quasi-égalité** (+6,6 pts attaque vs +6,5 pts défense).
3. **Mais, avant le match, c'est l'attaque le signal fiable.** D'une saison sur l'autre, les xG créés sont stables (**corrélation 0,78**) alors que les xG concédés se répètent beaucoup moins (**0,53**). Une fois l'attaque connue, la défense passée n'ajoute presque rien à la prévision des points futurs (t = −1,3, non significatif).
4. **Conclusion pratique :** la défense « pèse » autant que l'attaque dans le mécanisme du résultat, mais elle est **deux fois plus bruitée** et **deux fois moins dispersée** entre équipes. Elle mérite donc **moitié moins de poids** dans un modèle de pronostic — sauf si vous jouez « ne pas perdre » (1X / X2 / DNB), où elle redevient aussi importante que l'attaque.

---

## 2. Données et méthode

| Élément | Détail |
|---|---|
| Source | Understat (xG, xGA, xPTS par équipe-saison) |
| Échantillon | 172 équipes-saisons, 9 ligues-saisons, Big-5, 2024/25 + 2025/26 |
| Unité | **buts attendus par 90 minutes** (xG/90 et xGA/90) |
| Traitement | variables **centré es par ligue-saison** (effets fixes) : on compare des équipes entre elles dans une même ligue, pas des ligues entre elles |
| Modèle | Poisson par match : `λ_dom = k · μ · (xG90_dom/μ)^p · (xGA90_ext/μ)^q · hfa`, calibré sur les **xPTS** d'Understat (cible sans bruit de finition) |

**Point clé de cadrage.** Dans une ligue, `somme(xG) = somme(xGA)` : la moyenne de xG90 est **exactement** la moyenne de xGA90 (μ ≈ 1,55). Les deux métriques sont donc sur la **même échelle** : « +0,1 xG/90 » et « −0,1 xGA/90 » coûtent la même chose en xGD et sont directement comparables. Ce n'est pas vrai pour les buts marqués/encaissés réels.

**Deux faits structurants mesurés sur l'échantillon :**

| Dispersion intra-ligue | Valeur |
|---|---|
| Écart-type de xG90 (attaque) | **0,401** but/90 |
| Écart-type de xGA90 (défense) | **0,280** but/90 |

→ Les équipes se ressemblent **beaucoup moins en attaque qu'en défense** (dispersion +43 %). Autrement dit : il existe de vrais « monstres offensifs », beaucoup moins de « monstres défensifs ». Mécaniquement, l'attaque expliquera donc davantage les écarts de résultats **même si** son effet unitaire est identique.

---

## 3. Résultat 1 — À « coût xG égal » : l'attaque fait gagner, la défense fait ne pas perdre

Régressions sur les 172 équipes-saisons (variables centrées par ligue-saison) :

| Variable expliquée | b(xG90) | b(xGA90) | β* xG | β* xGA | R² |
|---|---|---|---|---|---|
| **Points / match** | **+0,695** (t 14,1) | **−0,614** (t −8,7) | **+0,61** | −0,38 | 0,84 |
| **Victoires / match** | **+0,258** (t 14,1) | −0,184 (t −7,0) | **+0,65** | −0,32 | 0,82 |
| **Défaites / match** | −0,179 (t −9,3) | **+0,246** (t +8,9) | −0,49 | **+0,46** | 0,77 |
| Nuls / match | −0,078 | −0,063 | −0,43 | −0,24 | 0,10 |

Lecture :
* **Victoires** : 1 but/90 de xG créé « vaut » **40 % de plus** que 1 but/90 de xG concédé en moins (0,258 vs 0,184).
* **Défaites** : c'est l'inverse — 1 but/90 concédé « coûte » **37 % de plus** que 1 but/90 non créé (0,246 vs 0,179).
* β* (coefficient standardisé) = poids réel dans la variance observée : l'attaque domine nettement pour les points (0,61 vs 0,38) et les victoires (0,65 vs 0,32) ; les deux sont à égalité sur les défaites.

**Effets marginaux exacts** (modèle de Poisson, terrain neutre, équipe moyenne vs équipe moyenne, +0,10 xG/90 vs −0,10 xGA/90) :

| Scénario | Δ P(victoire) | Δ P(ne pas perdre) | Δ P(clean sheet) |
|---|---|---|---|
| **+0,1 xG/90 (attaque)** | **+0,0249** | +0,0196 | 0 |
| **−0,1 xGA/90 (défense)** | +0,0205 | **+0,0254** | +0,0255 |
| **Rapport défense / attaque** | **0,82** | **1,30** | — |

Et selon le profil :

| Profil | Δ P(victoire) : attaque vs défense | Δ P(ne pas perdre) : attaque vs défense |
|---|---|---|
| Équipe moyenne, domicile | +0,0243 vs +0,0224 | +0,0171 vs +0,0248 (défense ×1,45) |
| Équipe moyenne, extérieur | +0,0245 vs +0,0180 (attaque ×1,36) | +0,0216 vs +0,0250 |
| **Équipe forte** (+0,5/−0,3), domicile | +0,0199 vs **+0,0237** (défense ×1,19) | +0,0111 vs **+0,0202** (défense ×1,82) |
| **Équipe faible** (−0,5/+0,3), extérieur | **+0,0219** vs +0,0117 (attaque ×1,87) | +0,0247 vs +0,0223 |

> **Règle :** une équipe déjà forte convertit mieux une amélioration **défensive** (elle gagne déjà ses matchs, elle transforme des nuls en victoires en encaissant moins). Une équipe faible n'améliore sa probabilité de gagner qu'en **attaquant**.

---

## 4. Résultat 2 — Dans la réalité, l'attaque pèse plus (parce qu'elle varie plus)

Comparaison à **1 écart-type** — c'est-à-dire l'écart réel entre deux équipes d'une même ligue (moyenne domicile + extérieur, contre adversaire moyen) :

| Profil | P(victoire) | P(nul) | P(défaite) | **P(ne pas perdre)** | Points/match |
|---|---|---|---|---|---|
| Équipe moyenne | 0,377 | 0,247 | 0,377 | 0,623 | 1,38 |
| **+1 SD d'attaque** (+0,40 xG/90) | 0,464 | 0,226 | 0,310 | **0,690** | 1,62 |
| **+1 SD de défense** (−0,28 xGA/90) | 0,430 | 0,259 | 0,311 | **0,689** | 1,55 |
| Les deux | 0,520 | 0,229 | 0,251 | 0,749 | 1,79 |

| Gain | P(victoire) | P(ne pas perdre) | Points/match |
|---|---|---|---|
| **1 SD d'attaque** | **+0,087** | +0,066 | **+0,240** |
| **1 SD de défense** | +0,053 | +0,065 | +0,172 |
| **Rapport défense / attaque** | **0,61** | **0,98** | **0,71** |

→ Pour **gagner** et pour **marquer des points**, l'attaque pèse **~1,4 à 1,6 fois** la défense.
→ Pour **ne pas perdre**, les deux se valent (rapport 0,98).

**Test du modèle Poisson.** Poids optimaux pour reproduire les points attendus : **p = 1,00 (attaque)** et **q = 1,05 (défense)** — des poids **quasi symétriques**. La symétrie est donc dans le « mécanisme » (1 unité d'écart à la moyenne en défense compte autant qu'en attaque), pas dans la dispersion. Corrélation avec les points réels : 0,918 avec les deux dimensions, **0,881** en ne gardant que l'attaque, **0,814** en ne gardant que la défense → **supprimer l'attaque fait plus mal que supprimer la défense**.

---

## 5. Résultat 3 — À xGD égal, le profil défensif ne rapporte pas plus de points… mais il est plus « sûr »

Simulation : deux équipes avec le même xGD (+0,4 par match), l'une qui le doit à l'attaque, l'autre à la défense.

| Profil (xGD = +0,4) | xG90 | xGA90 | P(victoire) | P(nul) | **P(ne pas perdre)** | Points/match |
|---|---|---|---|---|---|---|
| Tout par l'attaque | 1,95 | 1,55 | 0,464 | 0,226 | 0,690 | 1,62 |
| **Tout par la défense** | 1,55 | 1,15 | 0,455 | **0,263** | **0,718** | 1,63 |
| Moitié-moitié | 1,75 | 1,35 | 0,460 | 0,242 | 0,702 | 1,62 |

Même total de points, **mais** le profil défensif échange des victoires contre des nuls : **+2,8 points** de probabilité de ne pas perdre, −2,8 points de défaites. C'est exactement le profil qui rapporte sur les marchés **1X / X2 / « ne pas perdre » / DNB**, et celui qui plaît aux entraîneurs sous pression.

Symétriquement, avec un xGD de −0,4, un **trou défensif** coûte moins cher en points (−1,8 pt/saison) qu'un **trou offensif** : une équipe qui n'attaque pas arrache des 0-0.

---

## 6. Résultat 4 — Là où la défense perd : c'est un signal bruité (le point crucial pour le parieur)

65 équipes présentes dans les deux saisons (EPL, La Liga, Bundesliga, Ligue 1) :

| Stabilité d'une saison sur l'autre | Corrélation |
|---|---|
| **xG90 (créés) : S1 → S2** | **+0,78** |
| **xGA90 (concédés) : S1 → S2** | **+0,53** |
| xGD90 : S1 → S2 | +0,78 |

**Les xG concédés sont beaucoup moins persistants** : une saison défensive exceptionnelle est, pour une large part, de la chance (finition adverse, forme du gardien, petit nombre d'occasions concédées). Une saison offensive exceptionnelle, beaucoup moins.

Conséquence sur la prévision des points de la saison suivante :

| Modèle (signaux de la saison 1 → points de la saison 2) | R² | β* xG | β* xGA |
|---|---|---|---|
| xG90 seul | **0,534** | — | — |
| xGA90 seul | 0,320 | — | — |
| xG90 + xGA90 | 0,546 | **+0,635** (t = +5,6) | −0,145 (t = **−1,3**, non significatif) |
| Référence naïve : points de la saison 1 | 0,50 (corr 0,708) | | |

| Prédiction des défaites de la saison 2 | R² | β* xG | β* xGA |
|---|---|---|---|
| Défaites / match | 0,463 | **−0,635** (t = −5,1) | +0,066 (t = +0,5, nul) |

Corrélations avec les points de la saison suivante : **xG90 = +0,731**, xGA90 = −0,565, **xGD90 = +0,730**.

> **C'est le paradoxe de la question :** dans le match, la défense compte (presque) autant que l'attaque ; mais **avant** le match, votre estimation de la défense est bien moins fiable. Connaître l'attaque suffit : la défense passée n'ajoute quasiment rien (t = −1,3).

---

## 7. Conséquences pratiques

**a) Pondération dans un modèle (règle de shrinkage).**
Pour estimer la force d'une équipe, partez de l'écart à la moyenne de la ligue, puis appliquez un **poids de ~0,78 sur les xG créés** et **~0,53 sur les xG concédés** (les autocorrélations mesurées). Concrètement : **régressez la défense d'environ moitié vers la moyenne, l'attaque d'environ un quart.** C'est le gain le plus net et le plus simple.

**b) Selon le marché joué.**

| Marché | Pondération attaque : défense | Raison |
|---|---|---|
| **Victoire** (1 / 2), handicap −1, « gagne » | **~1,5 : 1** | +8,7 pts de P(win) pour 1 SD d'attaque vs +5,3 pts |
| **Ne pas perdre** (1X, X2, DNB, double chance) | **~1 : 1** | +6,6 vs +6,5 pts — quasi-égalité |
| **Over/Under buts** | attaque + défense de l'adversaire, poids symétriques (p ≈ q ≈ 1) | λ_seule = f(xG d'un côté, xGA de l'autre) |
| Favori à domicile | **défense ×1,5 à 1,8** sur « ne pas perdre » | elle transforme ses nuls en victoires |
| Outsider à l'extérieur | **attaque** | c'est le seul levier qui bouge P(win) |

**c) Le résumé à utiliser en priorité : le xGD (xG − xGA).**
Corrélation avec les points : **0,916** (vs 0,876 pour xG seul et −0,806 pour xGA seul), et **0,730** avec les points de la saison suivante. Le xGD reste le meilleur résumé en une variable — mais à **xGD égal**, retenez que le profil **défensif** produit plus de nuls et moins de défaites (intéressant pour le 1X, défavorable pour le « victoire » et l'over).

**d) Ne sur-réagissez jamais à une série défensive.** Un xGA exceptionnel sur 5-10 matchs régresse vers la moyenne deux fois plus vite que les xG créés. C'est le biais classique : « ils n'encaissent plus rien » est, statistiquement, beaucoup moins durable que « ils se créatent plein d'occasions ».

---

## 8. Limites

* Données **agrégées par saison** (pas match par match) : les effets marginaux sont calculés avec un modèle de Poisson calibré (p = q = 1, hfa = 1,12, 1 xG = 0,915 but — le ratio buts/xG observé sur l'échantillon), pas par régression logistique sur les xG de chaque match. Le calibrage reproduit les xPTS d'Understat à 0,033 point/match près (corrélation 0,996).
* xG et xGA sont corrélés (−0,70) : une équipe qui attaque beaucoup concède peu. Les coefficients sont estimés **jointement**, ce qui isole l'effet propre de chaque dimension, mais impose de la prudence sur les effets « toutes choses égales par ailleurs ».
* L'avantage du terrain n'est pas identifiable avec des bilans de saison (chaque équipe joue autant à domicile qu'à l'extérieur) : il est fixé à 1,12 (valeur standard du Big-5).
* Échantillon de 65 paires pour l'analyse de fiabilité : les écarts (0,78 vs 0,53) sont nets, mais à confirmer sur plus de saisons.
* Séries non traitées : blessures, mercato, calendrier, état de forme, et le fait que les xG concédés dépendent du niveau des adversaires rencontrés.
