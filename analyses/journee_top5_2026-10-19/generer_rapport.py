# -*- coding: utf-8 -*-
"""Génère le rapport markdown du bilan H2H de la dernière journée du top 5."""
import os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from donnees_h2h import MATCHES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bilan.md")

RAISONS_ZERO = {
    ("Fulham", "Hull City"): "Hull City n'était pas dans l'élite en 2024-25 ni en 2025-26 (deuxième division anglaise).",
    ("Tottenham", "Coventry City"): "Coventry City n'était pas dans l'élite en 2024-25 ni en 2025-26 (deuxième division anglaise).",
    ("Deportivo La Corogne", "Levante"): "Deportivo évoluait en deuxième division espagnole.",
    ("Osasuna", "Racing Santander"): "Racing Santander évoluait en deuxième division espagnole.",
    ("Málaga", "Real Sociedad"): "Málaga évoluait en deuxième division espagnole.",
    ("Frosinone", "Sassuolo"): "Frosinone évoluait en Serie B (relégué en 2024).",
    ("Werder Brême", "Paderborn"): "Paderborn évoluait en 2. Bundesliga.",
    ("Schalke 04", "Mayence"): "Schalke 04 évoluait en 2. Bundesliga.",
    ("Elversberg", "Augsbourg"): "Elversberg évoluait en 2. Bundesliga.",
    ("Le Mans", "Toulouse"): "Le Mans évoluait en Ligue 2.",
    ("Troyes", "Lens"): "Troyes évoluait en Ligue 2.",
}

for m in MATCHES:
    hw = aw = d = 0
    for s, th, ta, hs, as_ in m["h2h"]:
        if hs > as_:
            w = th
        elif as_ > hs:
            w = ta
        else:
            w = None
            d += 1
        if w == m["home"]:
            hw += 1
        elif w == m["away"]:
            aw += 1
    m.update(hw=hw, aw=aw, dr=d, n=len(m["h2h"]))
    m["fav"] = "home" if hw > aw else ("away" if aw > hw else None)
    if m["score"]:
        h, a = map(int, m["score"].split("-"))
        m["res"] = "H" if h > a else ("A" if a > h else "D")
        v = None
        if m["fav"] == "home":
            v = "ok" if m["res"] in ("H", "D") else "ko"
        elif m["fav"] == "away":
            v = "ok" if m["res"] in ("A", "D") else "ko"
        m["verdict"] = v
    else:
        m["verdict"] = None

played = [m for m in MATCHES if m["score"]]
pending = [m for m in MATCHES if not m["score"]]
applicable = [m for m in played if m["fav"]]
ok = [m for m in applicable if m["verdict"] == "ok"]
ko = [m for m in applicable if m["verdict"] == "ko"]
equal = [m for m in played if m["n"] > 0 and not m["fav"]]
zero = [m for m in played if m["n"] == 0]
rate = 100 * len(ok) / len(applicable)

LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
JOURNEE = {"Premier League": "7e journée", "La Liga": "9e journée", "Serie A": "7e journée",
           "Bundesliga": "6e journée", "Ligue 1": "7e journée"}
NOMS_JOUR = {"Premier League": "Premier League", "La Liga": "Liga", "Serie A": "Serie A",
             "Bundesliga": "Bundesliga", "Ligue 1": "Ligue 1"}

by_league = defaultdict(list)
for m in MATCHES:
    by_league[m["league"]].append(m)

stats = {}
for lg in LEAGUES:
    sub = [m for m in by_league[lg] if m["score"]]
    app = [m for m in sub if m["fav"]]
    o = [m for m in app if m["verdict"] == "ok"]
    k = [m for m in app if m["verdict"] == "ko"]
    stats[lg] = dict(joues=len(sub), app=len(app), ok=len(o), ko=len(k),
                     eq=len([m for m in sub if m["n"] > 0 and not m["fav"]]),
                     zero=len([m for m in sub if m["n"] == 0]),
                     att=len([m for m in by_league[lg] if not m["score"]]),
                     rate=(100 * len(o) / len(app)) if app else None)

dom = defaultdict(lambda: [0, 0])
for m in applicable:
    diff = abs(m["hw"] - m["aw"])
    dom[diff][0] += 1 if m["verdict"] == "ok" else 0
    dom[diff][1] += 1

fav_home = [m for m in applicable if m["fav"] == "home"]
fav_away = [m for m in applicable if m["fav"] == "away"]
ok_home = [m for m in fav_home if m["verdict"] == "ok"]
ok_away = [m for m in fav_away if m["verdict"] == "ok"]
base4 = [m for m in applicable if m["n"] == 4]
ok4 = [m for m in base4 if m["verdict"] == "ok"]
base2 = [m for m in applicable if m["n"] == 2]
ok2 = [m for m in base2 if m["verdict"] == "ok"]


def nom_fav(m):
    return m["home"] if m["fav"] == "home" else m["away"]


def plur(n, mot):
    return f"{n} {mot}" if n <= 1 else f"{n} {mot}s"


def score_txt(m):
    h, a = map(int, m["score"].split("-"))
    return f"{h}-{a}"


def fr(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def bloc(m):
    L = []
    L.append(f"### {m['home']} {m['score']} {m['away']}" if m["score"] else f"### {m['home']} – {m['away']}")
    L.append(f"*{NOMS_JOUR[m['league']]} · {m['date']}*\n")
    if m["n"] == 0:
        L.append(f"- Aucune confrontation en championnat sur les deux dernières saisons : "
                 f"{RAISONS_ZERO.get((m['home'], m['away']), 'les deux clubs ne se sont pas croisés dans la même division.')}")
        if m["score"]:
            L.append(f"\n**Verdict : ⚪ critère non applicable** — {m['home']} {m['score']} {m['away']}, "
                     f"mais la règle n'avait aucun historique pour se prononcer.")
        else:
            L.append("\n**Verdict : ⏳ à jouer** — match sans historique direct, donc sans signal.")
        return "\n".join(L)

    for season in ("2025-26", "2024-25"):
        parts = [f"{h} **{hs}-{as_}** {a}" for s, h, a, hs, as_ in m["h2h"] if s == season]
        if parts:
            L.append(f"- **{season}** — " + " ; ".join(parts))

    base = "base de 4 confrontations" if m["n"] == 4 else f"base de {m['n']} confrontations"
    if m["fav"]:
        L.append(f"\n**Bilan H2H : {plur(m['hw'], 'victoire')} {m['home']} · {plur(m['dr'], 'nul')} · "
                 f"{plur(m['aw'], 'victoire')} {m['away']}** → favori : **{nom_fav(m)}** ({base})")
    else:
        L.append(f"\n**Bilan H2H : {plur(m['hw'], 'victoire')} {m['home']} · {plur(m['dr'], 'nul')} · "
                 f"{plur(m['aw'], 'victoire')} {m['away']}** → **aucun favori** : égalité parfaite du nombre de victoires.")

    if not m["score"]:
        if m["fav"]:
            L.append(f"\n**Verdict : ⏳ à jouer** — la règle désigne **{nom_fav(m)}** (victoire ou nul).")
        else:
            L.append("\n**Verdict : ⏳ à jouer** — pas de favori, la règle ne tranche pas.")
    elif m["verdict"] == "ok":
        if m["res"] == "D":
            L.append(f"\n**Verdict : ✅ validé** — {score_txt(m)} : le nul sauve la double chance du favori.")
        else:
            L.append(f"\n**Verdict : ✅ validé** — {nom_fav(m)} s'impose ({score_txt(m)}).")
    elif m["verdict"] == "ko":
        L.append(f"\n**Verdict : ❌ contredit** — le favori {nom_fav(m)} s'incline "
                 f"({m['home']} {score_txt(m)} {m['away']}).")
    else:
        L.append(f"\n**Verdict : ⚪ critère non applicable** — historique équilibré, le match se termine {m['score']}.")
    return "\n".join(L)


def emoji(m):
    if not m["score"]:
        return "⏳ En attente"
    if m["n"] == 0 or not m["fav"]:
        return "⚪ Non applicable"
    return "✅ Validé" if m["verdict"] == "ok" else "❌ Contredit"


D = []
A = D.append

A("# Bilan à la loupe — la règle des confrontations directes")
A("## Dernière journée des 5 grands championnats européens · 16-19 octobre 2026\n")
A("**Règle testée :** « les équipes ayant remporté le plus de matchs dans les confrontations directes "
  "des 2 dernières années font victoire ou match nul dans le match du jour. »\n")
A("**Périmètre :** Premier League (7e journée), Liga (9e), Serie A (7e), Bundesliga (6e), Ligue 1 (7e) — "
  "soit 48 matchs, dont 45 terminés au moment de la rédaction.\n")
A("---\n")

A("## 1. Ce qu'il faut retenir\n")
A(f"- **{len(MATCHES)} matchs** composent cette dernière journée : 10 en Premier League, 10 en Liga, "
  "10 en Serie A, 9 en Bundesliga, 9 en Ligue 1.")
A(f"- **{len(played)} matchs sont d'ores et déjà joués** ; {len(pending)} se jouaient encore au moment de la rédaction "
  "(les trois du lundi).")
A(f"- Sur ces {len(played)} matchs, la règle ne peut se prononcer que sur **{len(applicable)}** : "
  f"{len(equal)} sont à égalité parfaite de victoires et {len(zero)} n'ont aucun historique "
  f"(clubs promus ou divisions différentes), soit **{fr(100*(len(equal)+len(zero))/len(played), 0)} % de la journée inexploitable**.")
A(f"- Quand elle se prononce, la règle est validée **{len(ok)} fois sur {len(applicable)}**, soit "
  f"**{fr(rate)} %** ({len(ko)} échecs).")
rates = sorted([(stats[lg]["rate"], lg) for lg in LEAGUES if stats[lg]["rate"] is not None], reverse=True)
A("- Le détail est très inégal : " + ", ".join(
    f"**{fr(r, 0)} % en {NOMS_JOUR[lg]}**" if i < len(rates) - 1 else f"et **{fr(r, 0)} % en {NOMS_JOUR[lg]}**"
    for i, (r, lg) in enumerate(rates)) + ".")
A(f"- Les favoris H2H à domicile s'en sortent nettement mieux (**{len(ok_home)}/{len(fav_home)}, "
  f"{fr(100*len(ok_home)/len(fav_home), 0)} %**) que les favoris à l'extérieur "
  f"(**{len(ok_away)}/{len(fav_away)}, {fr(100*len(ok_away)/len(fav_away), 0)} %**).\n")

A("---\n")
A("## 2. Comment la règle a été appliquée\n")
A("Trois précisions méthodologiques, indispensables pour lire les chiffres :\n")
A("1. **Fenêtre retenue :** les deux dernières saisons complètes, **2024-25 et 2025-26**, en **championnat uniquement**. "
  "Les coupes sont exclues (elles ajoutent des matchs isolés, souvent avec des rotations d'effectif). "
  "Comme aucune des affiches du jour n'oppose deux clubs déjà croisés en championnat cette saison, "
  "ajouter 2026-27 ne changerait rien : la fenêtre est propre, sans circularité.")
A("2. **Confrontations directes :** toutes les rencontres de championnat entre les deux clubs sur ces deux saisons, "
  "soit **4 matchs** quand les deux clubs étaient dans la même division les deux années, **2 matchs** quand l'un "
  "est monté ou descendu entre-temps, **0** quand ils n'ont jamais été dans la même division.")
A("3. **Décision :** le *favori H2H* est le club qui compte **strictement plus de victoires** que son adversaire. "
  "Le critère est validé si ce club **gagne ou fait match nul** (double chance). À égalité de victoires, il n'y a pas "
  "de favori : le critère ne dit rien, et on ne compte ni réussite ni échec.\n")

A("---\n")
A("## 3. Le tableau d'ensemble\n")
A("| Championnat | Matchs joués | Critère applicable | ✅ Validé | ❌ Contredit | Taux | Sans favori | Sans historique | En attente |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for lg in LEAGUES:
    s = stats[lg]
    r = f"{fr(s['rate'], 0)} %" if s["rate"] is not None else "—"
    A(f"| {lg} | {s['joues']} | {s['app']} | {s['ok']} | {s['ko']} | **{r}** | {s['eq']} | {s['zero']} | {s['att']} |")
A(f"| **Total** | **{len(played)}** | **{len(applicable)}** | **{len(ok)}** | **{len(ko)}** | **{fr(rate)} %** | "
  f"**{len(equal)}** | **{len(zero)}** | **{len(pending)}** |")
A("")
A("Lecture : la règle a fonctionné deux fois sur trois. C'est mieux qu'un tirage au sort, mais très loin d'un "
  "système automatique — et surtout, elle a été **ratée en Italie** et **parfaite en Espagne**, ce qui en dit long "
  "sur sa dépendance au contexte de chaque championnat.\n")

A("### Ce que dit l'écart de victoires\n")
A("| Écart de victoires H2H | Réussites | Total | Taux |")
A("|---|---:|---:|---:|")
for k in sorted(dom):
    a, t = dom[k]
    A(f"| {k} victoire{'s' if k > 1 else ''} d'écart | {a} | {t} | {fr(100*a/t, 0)} % |")
A("")
A("Contre-intuitif mais net : **les gros déséquilibres ne sont pas les signaux les plus fiables**. "
  "Les écarts de 3 victoires et plus n'ont rapporté que **2 réussites sur 5**, alors que les écarts d'une seule "
  "victoire ont tenu **8 fois sur 11**. Un 4-0 dans l'historique ne vaut pas un blanc-seing.\n")

A("---\n")
A("## 4. Les confrontations, une par une\n")

for lg in LEAGUES:
    s = stats[lg]
    r = f"{fr(s['rate'], 0)} %" if s["rate"] is not None else "—"
    A(f"\n### {lg} — {JOURNEE[lg]}\n")
    A(f"*{s['joues']} matchs joués · {s['app']} arbitrés par la règle · "
      f"{s['ok']} {'validé' if s['ok'] <= 1 else 'validés'} · "
      f"{s['ko']} {'contredit' if s['ko'] <= 1 else 'contredits'} · taux {r}*\n")
    A("| Match | Score | H2H (dom.-nul-ext.) | Favori | Verdict |")
    A("|---|---|---|---|---|")
    for m in by_league[lg]:
        score = m["score"] if m["score"] else "à jouer"
        fav = nom_fav(m) if m["fav"] else ("—" if m["n"] else "aucun historique")
        A(f"| {m['home']} – {m['away']} | {score} | {m['hw']}-{m['dr']}-{m['aw']} | {fav} | {emoji(m)} |")
    A("")
    for m in by_league[lg]:
        A(bloc(m))
        A("")

A("---\n")
A("## 5. Les trois matchs du lundi\n")
A("Trois rencontres fermaient la journée, le lundi 19 octobre. Elles n'étaient pas terminées au moment de la rédaction :\n")
for m in pending:
    if m["fav"]:
        A(f"- **{m['home']} – {m['away']}** ({m['date']}) : H2H {m['hw']}-{m['dr']}-{m['aw']} "
          f"({plur(m['aw'] if m['fav']=='away' else m['hw'], 'victoire')} pour {nom_fav(m)}, "
          f"{plur(m['dr'], 'nul')}) → favori **{nom_fav(m)}**. La règle demande une victoire ou un nul.")
    elif m["n"]:
        A(f"- **{m['home']} – {m['away']}** ({m['date']}) : H2H {m['hw']}-{m['dr']}-{m['aw']} → égalité parfaite, "
          f"**aucun favori** : la règle ne permet pas de pari.")
    else:
        note = ""
        if m["home"] == "Tottenham":
            note = (" À noter, hors championnat : les deux clubs se sont croisés en Coupe en septembre 2024 "
                    "(Coventry 1-2 Tottenham), un match non retenu dans le décompte.")
        A(f"- **{m['home']} – {m['away']}** ({m['date']}) : **aucun historique** commun en championnat sur deux ans "
          f"→ pas de signal.{note}")
A("")
A("Sur ces trois rencontres, la règle ne fournissait donc **qu'un seul pari exploitable** : la double chance "
  "sur le Rayo à Getafe. Deux matchs sur trois échappaient totalement au critère — un rappel utile de sa couverture réelle.\n")

A("---\n")
A("## 6. Les enseignements\n")
A("### Ce que la règle a bien vu\n")
A("- **Le Real Madrid** : 4 victoires en 4 confrontations contre Séville, le signal le plus net de la journée — "
  "résultat, 4-1. C'est le seul écart de 4 victoires du week-end.")
A("- **Le Bayern** (3 victoires, 1 nul contre Leipzig) : 6-1. **Arsenal** (2 victoires, 2 nuls à Forest) : 1-0. "
  "**Barcelone** (2 victoires, 2 nuls contre le Betis) : 5-2.")
A("- **Les nuls du favori** ont sauvé trois tickets : Leeds – Manchester United (1-1), Villarreal – Elche (0-0), "
  "Union Berlin – Dortmund (0-0). C'est précisément l'intérêt de la double chance par rapport au pari sec.")
A("- **Le Paris SG, Lyon, Marseille, Rome, Leverkusen, Francfort** : six favoris qui ont tenu leur rang sans frayeur.\n")
A("### Ce que la règle a raté\n")
A("- **Brighton 5-0 Crystal Palace** : Palace avait 3 victoires et 1 nul dans les 4 confrontations. Correction infligée.")
A("- **Monza 4-0 Cagliari** : Cagliari avait gagné les deux seules confrontations (2024-25). Le promu a écrasé le favori.")
A("- **Le Havre 1-3 Auxerre** : Le Havre avait 3 victoires et 1 nul sur 4. Défaite à domicile.")
A("- **Udinese 0-3 Lecce** : Udinese avait 3 victoires sur 4. Défaite 0-3 à domicile.")
A("- **Milan 3-2 Atalanta** : l'Atalanta avait 3 victoires et 1 nul, elle perd d'un but.")
A("- **Paris FC 4-3 Rennes** : Rennes avait gagné les deux confrontations de 2025-26.")
A("- **Gladbach 1-2 Hoffenheim**, **Bournemouth 2-0 Sunderland** (Sunderland n'avait qu'une victoire et un nul : "
  "base trop mince), **Venezia 1-0 Napoli** (base de 2 matchs seulement).\n")
A("### Le point qui compte pour la suite\n")
A("- **La Serie A est le contre-exemple parfait** : 1 réussite sur 5. Sur cette journée, l'historique récent y a été "
  "systématiquement démenti — promotions, changements d'entraîneurs et effectifs remaniés rendent les confrontations "
  "de référence peu prédictives.")
A(f"- **La qualité de l'échantillon compte plus que l'écart** : les bases de 4 confrontations ont tenu à "
  f"**{fr(100*len(ok4)/len(base4), 0)} %** ({len(ok4)}/{len(base4)}), les bases de 2 confrontations à "
  f"**{fr(100*len(ok2)/len(base2), 0)} %** ({len(ok2)}/{len(base2)}). Ne jouer la règle que lorsque les deux clubs "
  "ont passé deux saisons complètes dans la même division est déjà un filtre utile.")
A(f"- **Le critère ne couvre qu'un tiers de la journée** : {len(equal)+len(zero)} matchs sur {len(played)} étaient "
  "soit sans historique, soit à égalité parfaite. C'est une règle de *filtrage*, pas une méthode de pronostic "
  "universelle.\n")

A("---\n")
A("## 7. Limites\n")
A(f"- **Un seul week-end** : {len(applicable)} observations, c'est trop peu pour conclure statistiquement. "
  "Ce bilan décrit une journée, il ne démontre pas un avantage sur le long terme.")
A("- **Championnat uniquement** : les confrontations en coupe (Coupe de France, FA Cup, Carabao Cup, Copa del Rey, "
  "Coppa Italia, DFB-Pokal) ne sont pas intégrées. Elles sont rares mais peuvent modifier un décompte serré.")
A("- **Pas de pondération** : une victoire 4-0 de septembre 2024 pèse autant qu'une victoire 1-0 de mai 2026. "
  "Une version améliorée pondérerait par la récence et par l'écart de buts.")
A("- **Effectifs** : la règle ignore les transferts, les blessures et les changements d'entraîneur, qui expliquent "
  "précisément plusieurs des échecs (Monza, Venezia, Le Havre).")
A("- **Données** : matrices de résultats des saisons 2024-25 et 2025-26, recoupées avec les résultats de la journée "
  "publiés par les sources de référence de chaque championnat.\n")

A("---\n")
A("## Annexe — récapitulatif complet\n")
A("| # | Championnat | Match | Score | Confr. | V-N-D | Favori | Verdict |")
A("|---:|---|---|---|---:|---|---|---|")
for i, m in enumerate(MATCHES, 1):
    score = m["score"] if m["score"] else "à jouer"
    fav = nom_fav(m) if m["fav"] else "—"
    verdict = emoji(m).split(" ")[0]
    A(f"| {i} | {m['league']} | {m['home']} – {m['away']} | {score} | {m['n']} | {m['hw']}-{m['dr']}-{m['aw']} | {fav} | {verdict} |")
A("")
A("*Données détaillées : `bilan_h2h.csv`. Calculs reproductibles : `calculs.py`.*")
A("")
A("*Rapport rédigé le 19 octobre 2026 en fin de soirée (UTC). Les trois rencontres du lundi — Getafe-Rayo, "
  "Parma-Torino et Tottenham-Coventry — étaient encore en cours de jeu et ne sont donc pas intégrées au bilan chiffré ; "
  "elles figurent en section 5 avec le verdict du critère.*")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(D))
print("Rapport écrit :", OUT, len("\n".join(D)), "caractères")
print(f"Stats -> appl {len(applicable)} ok {len(ok)} ko {len(ko)} rate {rate:.1f}%")
