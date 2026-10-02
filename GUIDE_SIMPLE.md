# Comment analyser un match — version simple

Pas de formule. Une méthode, un outil, et quatre règles.

---

## L'idée en une phrase

**On ne regarde pas les buts marqués, on regarde les buts « mérités » (les xG).**
Une équipe qui gagne 1-0 avec 0,3 xG a eu de la chance, pas du talent. Les xG, eux,
se répètent d'une saison à l'autre — c'est ça qui les rend utiles pour parier.

Et l'étude a montré une chose importante :

> **Pour savoir qui va gagner, c'est l'attaque (xG) qui compte le plus.**
> **Pour savoir qui ne va pas perdre, la défense (xGA) compte autant.**
> **Et la défense est deux fois plus trompeuse que l'attaque** : une « défense de fer »
> observée sur 5 matchs est du bruit à 87 %.

Toute la méthode découle de ces trois lignes.

---

## La méthode : 4 gestes

### 1. Prenez 2 chiffres par équipe

Sur Understat ou FBref, pour les **10 à 15 derniers matchs** :

* **xG par match** → combien l'équipe se crée
* **xGA par match** → combien elle concède

C'est tout. Pas besoin des buts réels, pas besoin du classement.

### 2. Comparez à la moyenne de la ligue

La moyenne du Big-5 tourne autour de **1,55 xG par match et par équipe**.
Donc :

* Arsenal à 2,04 xG → **+33 %** par rapport à la moyenne en attaque
* Arsenal à 0,87 xGA → **−43 %** en défense (donc très solide)

### 3. Laissez l'outil faire le reste

Il transforme ces 4 chiffres en **buts attendus** pour chaque équipe, puis en
**probabilités** : victoire, nul, plus de 2,5 buts, les deux marquent, etc.

Le point clé : **il ne donne pas le même crédit aux deux chiffres.**
Il fait confiance à l'attaque et se méfie de la défense — exactement dans les
proportions mesurées par l'étude. Plus votre échantillon est court, plus il se méfie :

| Matchs regardés | Crédit à l'attaque | Crédit à la défense |
|---|---|---|
| 5 | 32 % | **13 %** |
| 10 | 49 % | 23 % |
| 15 | 59 % | 30 % |
| saison complète | 78 % | 53 % |

### 4. Comparez à la cote de votre bookmaker

L'outil affiche la **cote juste** (celle qui correspond vraiment à la probabilité).
Vous comparez avec la cote proposée. **C'est là que se gagne l'argent — nulle part ailleurs.**

---

## Comment lire le résultat

Le chiffre central est **l'écart de buts attendus** entre les deux équipes.
À partir de lui, tout se lit dans ce tableau :

| Écart de buts | Victoire domicile | Nul | Victoire extérieur | Cote juste du favori |
|---|---|---|---|---|
| −1,2 | 14 % | 20 % | **65 %** | 1,53 |
| −0,8 | 21 % | 23 % | **56 %** | 1,78 |
| −0,4 | 29 % | 25 % | **47 %** | 2,14 |
| **0** | **38 %** | **25 %** | **38 %** | 2,67 |
| +0,4 | **47 %** | 25 % | 29 % | 2,14 |
| +0,8 | **56 %** | 23 % | 21 % | 1,78 |
| +1,2 | **65 %** | 20 % | 14 % | 1,53 |

**Règle de lecture : 0,4 but d'écart ≈ 9 points de pourcentage.**
Un écart de +1 but fait passer le favori de 38 % à 61 % de chances.

### Pour le marché des buts

L'écart ne sert à rien ici. Ce qui compte, c'est le **total** des buts attendus :

| Buts attendus au total | Plus de 2,5 buts |
|---|---|
| 2,3 | 40 % |
| 2,7 | 51 % |
| 2,85 | 54 % |
| 3,3 | 64 % |

---

## Les 4 règles d'argent

**1. Ne jouez que si la cote dépasse la cote juste d'au moins 5 %.**
En dessous, c'est du bruit : le modèle n'est pas assez précis pour ça.
L'outil vous le dit en couleur : vert = jouable, orange = douteux, rouge = ne pas jouer.

**2. Misez 1 à 2 % de votre bankroll, jamais plus.**
L'outil calcule la mise exacte (un quart de Kelly). Exemple : avantage de 6 %
→ **1,40 € pour 100 € de bankroll**. C'est peu, c'est normal : c'est ce qui vous
garde en vie sur 500 paris.

**3. Choisissez le bon marché selon la question.**

| Votre question | Ce qui décide | Marché à jouer |
|---|---|---|
| « Qui gagne ? » | l'attaque, surtout | 1N2, handicap |
| « Qui ne perd pas ? » | attaque **et** défense à égalité | 1X, X2, DNB |
| « Combien de buts ? » | les deux attaques + les deux défenses | Over / Under |

À xGD égal, une équipe « défensive » rapporte **+2,8 points de « ne pas perdre »**.
Sur les marchés 1X/X2, elle est donc systématiquement sous-cotée. C'est l'un des
rares avantages structurels que l'étude a trouvé.

**4. Méfiez-vous des avantages énormes.**
Si l'outil affiche 20 % ou 30 % d'avantage, ce n'est pas une aubaine : c'est qu'il
manque une information (blessé, rotation, match sans enjeu). L'outil affiche alors
« AVANTAGE SUSPECT » au lieu de « BONNE COTE ».

---

## Les 3 pièges à éviter

* **Le classement.** Une équipe 4e peut avoir 8 points de chance. Les xG le voient,
  le classement non.
* **La série défensive.** « 4 clean sheets d'affilée » sur 5 matchs ne vaut que 13 %
  de crédit. C'est le piège numéro 1 du parieur.
* **Les buts réels.** Un 3-0 sur un penalty et deux contres ne dit rien de la force
  d'une équipe. Les xG, si.

---

## L'outil

```bash
cd Bilama54
python3 calculateur.py
```

Puis ouvrez la page affichée. Vous choisissez les deux équipes, vous entrez les cotes
de votre bookmaker, vous cliquez sur « Analyser ». Cinq ligues sont chargées
(Angleterre, Espagne, Allemagne, France, Italie), sur les données de la saison
2025/26.

Si vous avez des chiffres plus récents (les 5 ou 10 derniers matchs), dépliez
**« J'ai des chiffres plus récents »** et entrez-les : l'outil adaptera sa méfiance
à la taille de votre échantillon.

---

## D'où viennent les chiffres

* Les pourcentages de crédit (78 % / 53 %) viennent de [`RAPPORT_xG_vs_xGA.md`](RAPPORT_xG_vs_xGA.md) :
  c'est la stabilité mesurée des xG et des xGA entre deux saisons, sur 172 équipes du Big-5.
* La méthode a été testée sur 65 équipes : elle prédit mieux la saison suivante que
  « les points de la saison passée » (**−5 % d'erreur**, corrélation 0,739 contre 0,705).
* Les mathématiques complètes, si un jour vous les voulez : [`MODELE_xG_xGA.md`](MODELE_xG_xGA.md).
  Vous n'en avez pas besoin pour parier.

---

## Ce que l'outil ne sait pas faire

Il ne connaît pas les blessés, les compositions, la météo, ni l'enjeu du match.
Il ne voit que les xG. **C'est un point de départ, pas une réponse.** Son rôle est de
vous dire où le bookmaker se trompe peut-être — à vous de vérifier pourquoi avant de miser.
