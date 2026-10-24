# PPG Lab — être autonome de FootyStats

Mini-application **hors-ligne** (un seul fichier `index.html`, aucune dépendance, aucune requête réseau) qui :

1. calcule le **PPG** d'une équipe exactement comme FootyStats (global / domicile / extérieur / last 5-6-10) ;
2. applique la **heatmap 5 couleurs** (vert foncé, vert clair, jaune, orangé, rouge) avec des seuils que **tu** contrôles ;
3. rejoue ton **filtre valeur** (« PPG ≥ 3 et cote < 1,70 ») sur les matchs à venir ;
4. stocke tout dans ton navigateur (localStorage) avec export / import JSON et CSV.

## 0. Installation sur Android (PWA)

L'app est une **PWA** : elle s'installe comme une vraie application, avec icône, plein écran et démarrage hors-ligne.

1. Ouvre l'URL de l'app dans **Chrome** (ou Samsung Internet / Edge) sur le téléphone.
2. Menu **⋮ → « Ajouter à l'écran d'accueil »** (ou « Installer l'application », ou le bouton *Installer l'application* dans l'onglet *Méthode*).
3. L'icône **PPG Lab** apparaît avec tes autres apps ; elle s'ouvre sans barre d'adresse.

Détails techniques : `manifest.webmanifest` (icônes 192/512 + maskable, `display: standalone`, thème sombre) et `sw.js` (service worker cache-first) assurent l'installation et le mode avion. Interface adaptée au tactile : navigation à défilement horizontal, champs en 16 px (pas de zoom automatique), cibles ≥ 42 px, prise en compte des encoches (`safe-area`), tableaux à défilement horizontal.

⚠️ L'installation PWA exige **HTTPS** (ou `localhost`). Sur un simple fichier `file://`, l'app fonctionne mais sans installation ni cache.

⚠️ « Effacer les données du navigateur » supprime tes résultats : **exporte en JSON** avant (Réglages → Exporter).

## Lancer l'app

- Double-clique sur `index.html` (fonctionne sans serveur), ou
- `python3 -m http.server 8000` puis <http://localhost:8000>.

Sur mobile : ouvre le fichier dans le navigateur, puis « Ajouter à l'écran d'accueil ».

---

## 1. Le PPG, la vraie formule

**PPG = points ÷ matchs joués**, plafonné à 3,00 (3 pts victoire, 1 nul, 0 défaite).

Ce que dit le glossaire officiel de FootyStats (vérifié le 24/10/2026) sur l'affichage :

| Mode | Ce qui est affiché |
|---|---|
| **Défaut** | Match de championnat classique → **PPG domicile** de l'équipe qui reçoit et **PPG extérieur** de l'équipe qui se déplace. Coupe, barrage, match international ou **début de saison** → **PPG des 10 derniers matchs** (toutes compétitions). |
| Home/Away | Toujours PPG domicile / PPG extérieur |
| Overall | Toujours PPG global (domicile + extérieur) |
| Last 5 / 6 / 10 | PPG sur les 5, 6 ou 10 derniers matchs, **toutes compétitions confondues** |

Conséquences pratiques :

- Un PPG de **3,00 = 100 % de victoires** dans le contexte affiché. Sur 3 ou 4 journées seulement, c'est un échantillon fragile : l'app affiche donc **le nombre de matchs** à côté de chaque PPG.
- Deux équipes à 3,00 ne se valent pas : 3 matchs ≠ 9 matchs.
- Les valeurs « bizarres » (0,11 / 0,33 / 0,67 / 1,22 / 2,67) sont simplement des fractions exactes de points ; elles révèlent la taille de l'échantillon (9, 3, 3, 9, 3 matchs).

## 2. La logique des couleurs

FootyStats colore **chaque cellule de statistique** sur **5 niveaux**, du vert foncé (le plus favorable) au rouge (le moins favorable). Point important : **la grille chiffrée n'est publiée nulle part** sur le site (l'Academy dit seulement « chaque stat est colorée pour votre confort »), et les seuils sont **propres à chaque statistique** — 60 % n'a pas la même couleur en BTTS et en clean sheets.

Deux principes qui, eux, sont certains :

1. **Le sens dépend du pari visé.** Pour un marché « plus de buts » ou un PPG, une valeur haute est verte. Pour une stat où un chiffre haut est un mauvais signal, l'échelle s'inverse — le site l'écrit noir sur blanc pour sa Goal Heatmap : « *Red = High scoring. Yellow = Average. Green = Low scoring* ».
2. **C'est une échelle absolue par métrique**, pas un classement relatif entre équipes.

Ce que fait l'app : mêmes 5 niveaux, mêmes conventions, mais **des bornes transparentes et éditables** (onglet *Réglages*).

Bornes livrées par défaut — **calage raisonné, pas une copie officielle** :

| Famille | Vert foncé | Vert clair | Jaune | Orangé | Rouge |
|---|---|---|---|---|---|
| PPG | ≥ 2,00 | 1,60 – 1,99 | 1,20 – 1,59 | 0,80 – 1,19 | < 0,80 |
| Pourcentages | ≥ 70 % | 60 – 69 % | 50 – 59 % | 40 – 49 % | < 40 % |
| Cotes (inversé) | ≤ 1,30 | 1,31 – 1,60 | 1,61 – 2,00 | 2,01 – 2,60 | > 2,60 |

**Calibrer en 30 secondes** : ouvre une page FootyStats, repère une valeur de chaque couleur (par ex. un 3,00 vert foncé, un 1,50 vert clair, un 0,67 orange), puis ajuste les bornes jusqu'à ce que ces mêmes valeurs tombent dans les mêmes couleurs chez toi. Tes seuils sont sauvegardés automatiquement.

## 3. Le filtre valeur

Règle par défaut, identique à ta demande initiale :

> une équipe dont le **PPG ≥ 3,00** (PPG dans son contexte : domicile si elle reçoit) **et la cote < 1,70**, en **D1 ou D2** uniquement.

Réglages modifiables : PPG cible, tolérance, cote max, nombre minimum de matchs joués, restriction D1/D2, mode de calcul du PPG.

Le tableau du filtre **explique chaque rejet** (`PPG 1.00`, `cote 6.50`, `division hors D1/D2`, `échantillon < 3`), pour que tu voies pourquoi un match ne sort pas.

## 4. Saisie des données

**Formulaire** : date, compétition, division (D1 / D2 / D3 / Coupe), équipes, score.

**CSV / collage** — une ligne par match, séparateur `;`, `,` ou tabulation :

```
date;competition;division;domicile;exterieur;buts_dom;buts_ext
2026-08-16;Ligue 1;1;Paris SG;Nantes;3;1
2026-08-16;Ligue 1;1;Lyon;Lens;0;0
```

L'en-tête est optionnel (les lignes qui ne commencent pas par une date `AAAA-MM-JJ` sont ignorées). Import d'un export JSON, export JSON et CSV depuis *Réglages*.

## 5. Limites assumées

- **Pas de scraper** : l'app ne va pas chercher FootyStats (conditions d'utilisation + aucune API publique gratuite). Tu saisis les résultats une fois, l'app calcule tout le reste — c'est ça, l'autonomie.
- **PPG ≠ niveau réel** : dépend de l'adversaire, du calendrier, des blessures. Un 3,00 sur 3 matchs contre des mal classés ne vaut pas un 3,00 sur 9 journées.
- **Montées/descentes** : mélanger deux saisons dans le même jeu de données fausse les PPG globaux — utilise l'export JSON pour archiver et repartir à zéro.
- Les cotes bougent : la cote stockée est celle du moment de la saisie.

## 6. Vérifications

Test automatisé (jsdom) sur le fichier livré, 16 assertions, 0 erreur :

- 12 matchs chargés → Nord FC 6 MJ, 18 pts, PPG global 3,00 / dom. 3,00 / ext. 3,00 ; Sud FC 1 pt, PPG 0,17 ;
- couleurs : 3,00 → vert foncé, 0,17 → rouge ;
- filtre : Nord FC (dom., 3,00) à 1,45 → **retenu** ; Ouest FC à 6,50 → **rejeté** ; cote **1,70 pile → rejetée** (strictement inférieure) ;
- import CSV, persistance localStorage, changement de mode PPG, réinitialisation.

Un exemple d'analyse produite à la main (avant l'app) : `../analyses/2026-10-25_ppg-3_cote-moins-1.70.md`.
