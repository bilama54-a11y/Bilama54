# Filtre FootyStats — PPG 3,00 + cote < 1,70

**Source :** footystats.org (pages « Matchs du jour » / « Tomorrow » / jour suivant)
**Date de consultation :** 24 octobre 2026
**Filtre appliqué :** au moins une équipe évoluant en **1ʳᵉ ou 2ᵉ division** dont le **PPG affiché est exactement 3,00**, et **cote 1X2 de cette équipe < 1,70**.

---

## 1. Ce que veut dire « PPG 3,00 » sur FootyStats (important)

Sur les listes de matchs, FootyStats affiche par défaut le **PPG « Home vs Away »** :
- **PPG domicile** pour l'équipe qui reçoit,
- **PPG extérieur** pour l'équipe qui se déplace.

Vérification faite sur les pages H2H :
- Arsenal – Everton : `3.00 WWW` (Arsenal, 3 matchs à domicile, 3 victoires) / `1.00 DDD` (Everton, 3 déplacements, 3 nuls)
- FC Barcelone – Real Madrid : `3.00 WWWW` (Barça à domicile, 4/4) / `1.50 WLWL` (Real à l'extérieur, 2 victoires 2 défaites)

👉 Un PPG de 3,00 = **100 % de victoires** dans ce contexte (domicile ou extérieur). C'est donc un échantillon court (3 à 5 matchs) : à prendre comme un signal de forme, pas comme une garantie.

---

## 2. Matchs qui passent le filtre (D1 / D2, hommes)

| # | Compétition (division) | Match | Équipe à PPG 3,00 | PPG | Cote 1X2 | Cote adverse | Nul | Horaire affiché |
|---|---|---|---|---|---|---|---|---|
| 1 | Premier League (D1, Angleterre) | Aston Villa – **Manchester City** | Manchester City (ext.) | 3,00 | **1,52** | 4,70 | 4,30 | sam. 7:30 |
| 2 | Premier League (D1, Angleterre) | **Arsenal** – Everton | Arsenal (dom.) | 3,00 | **1,44** | 7,00 | 4,35 | sam. 10:00 |
| 3 | Bundesliga (D1, Allemagne) | **RB Leipzig** – Elversberg | RB Leipzig (dom.) | 3,00 | **1,42** | 6,20 | 5,25 | sam. 9:30 |
| 4 | Segunda División (D2, Espagne) | **Almería** – Real Oviedo | Almería (dom.) | 3,00 | **1,58** | 4,65 | 3,85 | sam. 15:00 |
| 5 | Serie A (D1, Italie) | **Inter Milan** – Fiorentina | Inter (dom.) | 3,00 | **1,25** | 7,50 | 5,35 | dim. 7:30 |
| 6 | Serie B (D2, Italie) | **Palermo** – Carrarese | Palermo (dom.) | 3,00 | **1,38** | 5,45 | 4,20 | dim. 10:00 |
| 7 | La Liga (D1, Espagne) | **FC Barcelone** – Real Madrid | Barcelone (dom.) | 3,00 | **1,61** | 4,00 | 5,45 | dim. 16:00 |

Liens H2H :
1. https://footystats.org/england/manchester-city-fc-vs-aston-villa-fc-h2h-stats
2. https://footystats.org/england/arsenal-fc-vs-everton-fc-h2h-stats
3. https://footystats.org/germany/rasen-ballsport-leipzig-vs-sv-07-elversberg-h2h-stats
4. https://footystats.org/spain/ud-almeria-vs-real-oviedo-h2h-stats
5. https://footystats.org/italy/fc-internazionale-milano-vs-acf-fiorentina-h2h-stats
6. https://footystats.org/italy/us-citta-di-palermo-vs-carrarese-calcio-h2h-stats
7. https://footystats.org/spain/fc-barcelona-vs-real-madrid-cf-h2h-stats

---

## 3. PPG 3,00 mais cote trop haute (hors filtre)

| Compétition | Match | Équipe à PPG 3,00 | Cote | Commentaire |
|---|---|---|---|---|
| Ligue 2 (D2, France) | Saint-Étienne – Nantes | Saint-Étienne (dom.) | 1,73 | Raté de 3 centièmes |
| 2. Bundesliga (D2, Allemagne) | Hertha BSC – Arminia Bielefeld | Hertha (dom.) | 1,77 | Légèrement au-dessus |
| Bundesliga (D1, Allemagne) | SC Freiburg – Bayern Munich | Freiburg (dom.) | 6,25 | 100 % à domicile mais adversaire = Bayern (Bayern à 1,37) |

---

## 4. Foot féminin (si tu veux l'inclure)

Le filtre PPG 3,00 existe aussi en D1 féminine :
- **Chelsea Women** (extérieur, WSL) — PPG 3,00, cote **1,08** → passe le filtre
- Manchester City Women (extérieur, WSL) — PPG 3,00, **pas de cote affichée** par FootyStats
- Everton Women (domicile, WSL) — PPG 3,00 mais cote 2,05 → hors filtre

Je les ai exclus du tableau principal (foot masculin).

---

## 5. Limites de cette extraction

- FootyStats ne propose le filtre PPG/cote que dans son outil « Match Filter » **en JavaScript** (résultats réservés/limités à 25 et non accessibles sans compte) ; l'extraction a donc été faite en lisant les pages de matchs jour par jour.
- Sur ces pages, seuls certains pays sont **dépliés avec PPG + cotes** : Angleterre, France, Allemagne, Italie, Espagne, Écosse (D1 et D2). Les autres championnats (Belgique, Portugal, Pays-Bas, Turquie, Brésil, Argentine, etc.) sont listés mais **repliés** : leurs matchs ne sont pas vérifiables en une passe.
- Les cotes sont celles affichées par FootyStats au moment de la consultation (elles bougent).
- Les horaires sont ceux affichés par FootyStats (fuseau du site, indiqué −07:00 sur la page) ; les pages H2H les affichent 3 h plus tôt. Vérifie l'heure exacte sur la page du match.

**Pour étendre :** indique-moi les championnats à ajouter (ex. Belgique D1, Portugal D1, Eredivisie, Süper Lig, Brésil Série A/B…) et je déroule le même filtre ligue par ligue.
