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

### Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `RAPPORT_xG_vs_xGA.md` | rapport complet (résultats, tableaux, conséquences pratiques, limites) |
| `analyse_xg_xga.py` | script d'analyse (bibliothèque standard uniquement) |
| `data/understat_team_seasons.csv` | données : 172 équipes-saisons, Big-5, 2024/25 + 2025/26 (Understat) |
| `resultats_xg_xga.txt` | sortie brute du script |

Reproduire :

```bash
python3 analyse_xg_xga.py
```
