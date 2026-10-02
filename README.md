# Bilama54
Parieur sportif

## Analyse : xG vs xGA — lequel pèse le plus ?

**Question :** entre les xG (occasions créées) et les xGA (occasions concédées),
lequel pèse le plus sur une victoire, et lequel contribue le plus à ne pas perdre ?

**Réponse courte :** l'attaque (xG) fait gagner, la défense (xGA) fait ne pas perdre
— mais l'attaque est un signal deux fois plus fiable avant le match.

| Marché | Pondération attaque : défense |
|---|---|
| Victoire (1 / 2) | ~1,5 : 1 |
| Ne pas perdre (1X, X2, DNB) | ~1 : 1 |

Détail, méthode et chiffres : [`RAPPORT_xG_vs_xGA.md`](RAPPORT_xG_vs_xGA.md)

## La formule de match

```
A = (xG90/μ)^0,78        force d'attaque        D = (xGA90/μ)^0,53   faiblesse défensive
λ_dom = 0,915 · μ · A_dom · D_ext · 1,12        λ_ext = 0,915 · μ · A_ext · D_dom / 1,12
```

Les exposants **0,78** et **0,53** sont les fiabilités mesurées des deux signaux : ils
règlent le shrinkage (la défense, deux fois plus bruitée, est deux fois plus ramenée vers
la moyenne). Formule complète, table de lecture, backtest (2024/25 → 2025/26) et règles de
mise : [`MODELE_xG_xGA.md`](MODELE_xG_xGA.md)

### Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `MODELE_xG_xGA.md` | **la formule** : constantes, ratings, λ, probabilités, edge/Kelly, validation |
| `RAPPORT_xG_vs_xGA.md` | étude : résultats, tableaux, conséquences pratiques, limites |
| `modele_xg.py` | le modèle de match (1N2, 1X, Over/Under, BTTS, value, Kelly) + backtest |
| `analyse_xg_xga.py` | script de l'étude (bibliothèque standard uniquement) |
| `data/understat_team_seasons.csv` | données : 172 équipes-saisons, Big-5, 2024/25 + 2025/26 (Understat) |

Reproduire :

```bash
python3 analyse_xg_xga.py    # l'étude
python3 modele_xg.py         # la formule + backtest + tables
```
