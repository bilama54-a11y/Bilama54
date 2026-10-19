# Comment améliorer la stat

*Note méthodologique rattachée au bilan H2H du 16-19 octobre 2026 — 19 octobre 2026*

Le bilan affiche **67,9 %** (19 réussites sur 28 matchs arbitrés). La question « comment améliorer la stat » a deux réponses très différentes, et il faut les séparer :

1. **faire monter le chiffre** — en filtrant les matchs où la règle marche le mieux ;
2. **rendre le chiffre fiable** — parce qu'à 28 observations, un 67,9 % ne prouve presque rien.

La seconde réponse est plus importante que la première. Ce document donne les deux, chiffres à l'appui.

---

## 1. Le problème de fond : 67,9 % n'est pas encore une statistique

Sur 28 observations, un taux de 67,9 % a un intervalle de confiance à 95 % de **[50,6 % ; 85,2 %]**. Autrement dit : avec ces données, la règle peut aussi bien valoir 51 % (inutile) que 85 % (excellente). Le test binomial donne **p = 0,087** — au-dessus du seuil de 0,05, donc on ne peut pas rejeter l'hypothèse « la règle ne vaut pas mieux que le hasard ».

| Ce qu'on veut savoir | Nombre de paris nécessaires |
|---|---:|
| Taux à ±10 points | **84** |
| Taux à ±5 points | **334** |
| Taux à ±3 points | **929** |

À raison de ~28 paris par journée dans le top 5, il faut donc **environ 11 journées** pour descendre à ±10 points, et **une saison entière** pour approcher ±5 points. Tant qu'on reste sur un week-end, toute variation de ±8 points d'un match à l'autre n'est que du bruit.

**Conséquence pratique :** ne pas modifier la règle sur la base de ce seul week-end. Le risque est de régler la règle sur les 9 échecs observés, c'est-à-dire d'apprendre par cœur le passé.

---

## 2. Le résultat le plus embarrassant : la règle bat à peine « domicile »

C'est le test que tout le monde oublie. Sur les **28 mêmes matchs**, si on parie bêtement la double chance du club qui reçoit, on obtient :

| Pari | Réussites | Taux |
|---|---:|---:|
| **La règle H2H** | **19 / 28** | **67,9 %** |
| « Toujours le domicile » (mêmes 28 matchs) | 18 / 28 | 64,3 % |
| « Toujours le domicile » (45 matchs joués) | 27 / 45 | 60,0 % |

**La règle apporte une seule réussite de plus qu'un pari aveugle sur le terrain.** Ce n'est pas rien — mais ce n'est pas un avantage démontrable, et il faut le dire clairement : sur ce week-end, le critère H2H n'a pas fait beaucoup mieux que de cocher systématiquement la double chance du club qui reçoit. Tout l'écart tient dans quelques bons choix (Paris SG à Strasbourg, Marseille à Angers, Real Madrid contre Séville) compensés par autant de mauvais (Crystal Palace à Brighton, Cagliari à Monza).

C'est le **témoin** à afficher systématiquement : sans lui, un taux de 68 % ne dit pas si la règle discrimine quoi que ce soit, ou si elle capte simplement l'avantage du terrain, qui vaut déjà ~60 % en moyenne dans le top 5.

---

## 3. Les fausses bonnes idées (testées, et elles échouent)

### 3.1 « Ne jouer que les gros écarts » — c'est l'inverse

L'intuition dit : plus l'écart de victoires est large, plus le signal est fort. Les données disent le contraire.

| Écart de victoires | Réussites | Taux |
|---|---:|---:|
| 1 victoire | 8 / 11 | 73 % |
| 2 victoires | 9 / 12 | 75 % |
| **3 victoires ou plus** | **2 / 5** | **40 %** |

Un 4 victoires-0 défaite sur deux ans (Real Madrid face à Séville) tient effectivement la route, mais un 3 victoires-1 nul (Crystal Palace à Brighton, Le Havre contre Auxerre) peut parfaitement se retourner. **Filtrer sur l'écart ≥ 3 dégrade la stat.**

### 3.2 « Privilégier les bases de 2 confrontations » — mirage à 5/5

Le croisement des deux variables le montre immédiatement :

| | Base de 2 | Base de 4 |
|---|---:|---:|
| **Favori à domicile** | **5/5 (100 %)** | 6/9 (67 %) |
| **Favori à l'extérieur** | 0/4 (0 %) | 8/10 (80 %) |

Un filtre qui donne 100 % d'un côté et 0 % de l'autre, à quatre matchs d'écart, ne mesure rien : c'est du bruit d'échantillonnage. La cellule « domicile + base 2 » est un **piège classique** — 5 matchs, aucun échec, cote minimale 1,00. La présenter comme la règle à suivre serait une faute.

### 3.3 « Exclure la Serie A » — la tentation du sur-apprentissage

En retirant l'Italie : **18/23 = 78,3 %** (p = 0,011, le seul résultat qui passerait le seuil naïf). Sauf que :

- ce filtre a été choisi **après** avoir vu les résultats, sur le championnat qui s'est le plus mal comporté ;
- j'ai testé **11 variantes** dans cette note : en corrigeant pour tests multiples (seuil 0,05 / 11 = 0,0045), **aucune ne passe** ;
- 5 matchs italiens, c'est un échantillon de rien. Un week-end où Monza et Lecce s'imposent suffit à faire basculer le classement des championnats.

La Serie A vaut 20 % cette semaine. Rien ne dit qu'elle vaudra 20 % la semaine prochaine.

---

## 4. Ce qui marche vraiment (les trois leviers)

### Levier 1 : la condition de terrain — le seul signal robuste

| | Réussites | Taux | IC95 | Cote minimale |
|---|---:|---:|---:|---:|
| Favori **à domicile** | 11 / 14 | **78,6 %** | ±21,5 | **1,27** |
| Favori à l'extérieur | 8 / 14 | 57,1 % | ±25,9 | 1,75 |

21,5 points d'écart entre les deux, et cela recoupe un fait de base du football : l'avantage du terrain vaut 15 à 20 points de pourcentage en double chance. La règle H2H, quand elle désigne un favori qui joue **chez lui**, empile deux avantages qui vont dans le même sens. Quand elle désigne un favori **à l'extérieur**, elle les met en opposition.

C'est le seul filtre à retenir, et il est théoriquement défendable — pas seulement statistiquement observé.

### Levier 2 : pondérer la saison récente

Pondérer 2025-26 double et 2024-25 simple produit deux effets :

- le taux monte légèrement : **21/30 = 70,0 %** contre 67,9 % ;
- et la **couverture progresse** : 30 matchs arbitrés au lieu de 28, parce que la pondération départage les égalités que le comptage brut laissait sans favori.

Les quatre paris modifiés :

| Match | Score | Pari brut | Pari pondéré | Résultat du pari pondéré |
|---|---|---|---|---|
| Brentford – Liverpool | 1-2 | Liverpool | *aucun* | (retiré) |
| Valencia – Athletic Bilbao | 0-0 | *aucun* | Valencia | ✅ |
| Bologna – Inter | 1-3 | *aucun* | Inter | ✅ |
| Juventus – Lazio | 0-3 | *aucun* | Lazio | ✅ |

Trois trous comblés, tous gagnants. C'est le levier le plus rentable en volume, et il a une justification claire : **un effectif change de 30 à 50 % en deux ans**, donc un match de mai 2025 en dit moins long qu'un match de mars 2026.

### Levier 3 : départager les égalités par la différence de buts

Les 7 matchs à égalité de victoires (au comptage brut) étaient jusqu'ici laissés de côté. En les départageant par la différence de buts cumulée dans les confrontations : **3 réussites sur 4** (les 3 autres restent à égalité de buts et restent écartés). Combiné à la pondération, ce départage fait passer la couverture de 30 à **35 matchs** — soit +25 % par rapport à la v1, à taux quasi identique (68,6 %).

Là encore, 4 observations ne prouvent rien, mais le principe est sain : à victoires égales, la différence de buts est une mesure de dominance plus fine que le décompte binaire.

---

## 5. La vraie question : le taux, ou le rendement ?

C'est le point que le bilan ne traite pas encore, et c'est celui qui décide si la règle rapporte de l'argent.

**Un taux de réussite ne suffit pas. Il faut le comparer à la cote.**

La cote minimale pour être à l'équilibre est **1 / taux**. Autrement dit :

| Segment | Taux | Cote minimale pour ne pas perdre |
|---|---:|---:|
| Règle brute | 67,9 % | **1,47** |
| Favori à domicile | 78,6 % | **1,27** |
| Domicile + écart ≤ 2 | 81,8 % | **1,22** |

Or, sur une double chance de favori, les cotes réelles tournent souvent autour de **1,20 à 1,40**. Conclusion : même à 68 % de réussite, **la règle est probablement perdante** si la cote moyenne est inférieure à 1,47 — ce qui est le cas dès que le favori est un gros club. Un pari à 1,25 réussi 68 fois sur 100 rapporte 85 unités pour 100 engagées : **–15 %**.

C'est le piège classique du parieur : confondre « je gagne souvent » et « je gagne de l'argent ». La double chance est un marché à forte probabilité et à faible cote — exactement l'endroit où un taux de 68 % peut rimer avec perte.

**Ce qu'il faut donc enregistrer à partir de maintenant :** pour chaque pari, la cote réelle au moment de la prise, puis le rendement :

> rendement = (somme des cotes des paris gagnants − nombre de paris) / nombre de paris

Tant que ce chiffre n'est pas positif sur 200+ paris, la règle reste une observation, pas une stratégie.

---

## 6. Une règle v2, et ce qu'elle donnerait

En combinant les trois leviers — pondération de la saison récente, départage par la différence de buts, et filtre « favori à domicile » — on obtient :

| Règle | Paris | Réussites | Taux | Cote minimale | Couverture |
|---|---:|---:|---:|---:|---:|
| v1 — brute | 28 | 19 | 67,9 % | 1,47 | 62 % des matchs |
| v2 — pondérée + départage | 35 | 24 | 68,6 % | 1,46 | 78 % des matchs |
| **v2 — pondérée + départage + domicile** | **17** | **13** | **76,5 %** | **1,31** | **38 % des matchs** |

La v2 « domicile » gagne 8,6 points de taux mais **perd la moitié du volume** : 17 paris sur 45 matchs, soit environ 10 par journée dans le top 5. C'est le compromis à trancher consciemment : moins de paris, meilleure réussite, mais un échantillon qui mettra deux fois plus longtemps à devenir concluant.

Et surtout : **ne pas adopter la v2 sur la foi de ce week-end.** Elle est construite sur les mêmes 45 matchs qui ont servi à la tester. Sa vraie évaluation demande un jeu de données séparé.

---

## 7. Le protocole pour trancher (la partie qui manque au bilan)

Pour transformer 67,9 % en statistique solide, il faut quatre choses :

1. **Backtester sur 5 saisons.** Les matrices de résultats Wikipédia permettent de reconstruire les confrontations de 2021-22 à 2025-26 pour les cinq championnats, soit ~9 000 matchs et ~5 500 paris applicables. C'est un script de collecte, pas un travail impossible — et c'est la seule façon d'obtenir des intervalles de confiance utiles.
2. **Pré-enregistrer la règle.** Écrire la v2 avant de la tester, puis la valider sur une saison tenue à l'écart (par exemple 2025-26), sans retoucher les paramètres en cours de route. Tout ajustement après coup doit être documenté comme tel.
3. **Corriger les tests multiples.** Onze variantes testées, c'est onze occasions de trouver un faux positif. Le seuil à appliquer est 0,0045, pas 0,05.
4. **Enregistrer les cotes.** Sans cotes, impossible de distinguer une règle rentable d'une règle qui gagne souvent en perdant de l'argent.

---

## 8. Au-delà du H2H : ce qui ferait vraiment progresser le taux

Le H2H sur deux ans est un signal faible par construction : entre deux saisons, un club change d'entraîneur, de système et d'un tiers de son effectif. Si l'objectif est un taux nettement supérieur à 70 %, ce sont d'autres variables qu'il faut ajouter :

| Variable | Pourquoi elle compte | Disponibilité |
|---|---|---|
| **Forme sur 5 matchs** | Capte l'état réel de l'équipe, que le H2H ignore | Facile |
| **Buts attendus (xG) sur 5 matchs** | Distingue une bonne série chanceuse d'une vraie domination | Moyenne |
| **Absences / rotations** | Un titulaire en moins vaut souvent plus que 4 confrontations | Difficile |
| **Jours de repos** | Un club sortant d'une coupe européenne est fragilisé | Facile |
| **Enjeu** | Une équipe déjà sauvée ou déjà condamnée ne joue pas pareil | Facile |
| **Cote de clôture** | Le marché intègre tout ; battre la cote est le seul vrai test | Facile |

La combinaison la plus prometteuse n'est pas « H2H + un autre filtre », mais **H2H comme variable secondaire** dans un modèle qui pèse d'abord la forme et les absences. Le H2H apporte une information résiduelle — la mémoire d'un déséquilibre structurel, comme Real Madrid–Séville — que la forme ne capte pas.

---

## 9. En résumé

| Priorité | Action | Gain attendu |
|---|---|---|
| 1 | Afficher le témoin « domicile seul » à côté de chaque taux | Évite de s'enthousiasmer pour un faux avantage |
| 2 | Enregistrer les cotes et calculer le rendement | Distingue « gagne souvent » de « gagne de l'argent » |
| 3 | Backtester 5 saisons | Réduit l'intervalle de confiance de ±17 à ±1,2 point |
| 4 | Filtrer sur « favori à domicile » | +8 à +10 points de taux, moitié moins de paris |
| 5 | Pondérer la saison récente + départage par différence de buts | +25 % de volume à taux constant |
| 6 | Ne **pas** filtrer sur l'écart ≥ 3 ni sur l'exclusion de la Serie A | Ces filtres dégradent ou sont du sur-apprentissage |

Le message central tient en une phrase : **le chiffre à améliorer n'est pas 67,9 %, c'est la taille de l'échantillon.** Tout le reste — les filtres, les variantes, les segments — est du bruit tant qu'on juge sur 28 matchs.

---

*Tous les chiffres de cette note sont reproductibles avec `python3 variantes.py`, qui relit `donnees_h2h.py` et recalcule chaque variante.*
