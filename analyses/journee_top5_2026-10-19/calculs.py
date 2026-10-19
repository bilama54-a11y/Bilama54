# -*- coding: utf-8 -*-
"""Calcule le bilan du critère H2H et génère le rapport markdown + le CSV."""
import csv, os, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from donnees_h2h import MATCHES

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

RAISONS_ZERO = {
    ("Fulham", "Hull City"): "Hull City n'était pas dans l'élite en 2024-25 ni en 2025-26 (deuxième division).",
    ("Tottenham", "Coventry City"): "Coventry City n'était pas dans l'élite en 2024-25 ni en 2025-26 (deuxième division).",
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


def analyze(m):
    hw = aw = d = 0
    for season, th, ta, hs, as_ in m["h2h"]:
        if hs > as_:
            winner = th
        elif as_ > hs:
            winner = ta
        else:
            winner = None
            d += 1
        if winner == m["home"]:
            hw += 1
        elif winner == m["away"]:
            aw += 1
    if m["score"] is None:
        status = "pending"
        res = None
    else:
        h, a = [int(x) for x in m["score"].split("-")]
        res = "H" if h > a else ("A" if a > h else "D")
        status = "played"

    if hw > aw:
        fav = "home"
    elif aw > hw:
        fav = "away"
    else:
        fav = None

    verdict = None
    if status == "played" and fav:
        if fav == "home":
            verdict = "ok" if res in ("H", "D") else "ko"
        else:
            verdict = "ok" if res in ("A", "D") else "ko"

    m.update(hw=hw, aw=aw, dr=d, n=len(m["h2h"]), fav=fav, res=res, status=status, verdict=verdict)
    return m


for _m in MATCHES:
    analyze(_m)

played = [m for m in MATCHES if m["status"] == "played"]
pending = [m for m in MATCHES if m["status"] == "pending"]
applicable = [m for m in played if m["fav"]]
ok = [m for m in applicable if m["verdict"] == "ok"]
ko = [m for m in applicable if m["verdict"] == "ko"]
equal = [m for m in played if m["n"] > 0 and not m["fav"]]
zero = [m for m in played if m["n"] == 0]

print(f"Matchs: {len(MATCHES)} | joués {len(played)} | en attente {len(pending)}")
print(f"Critère applicable: {len(applicable)} | respecté {len(ok)} | contredit {len(ko)} | taux {100*len(ok)/len(applicable):.1f}%")
print(f"Historique équilibré (pas de favori): {len(equal)} | aucun historique: {len(zero)}")

by_league = defaultdict(lambda: dict(app=0, ok=0, ko=0, eq=0, zero=0, pend=0))
for m in MATCHES:
    b = by_league[m["league"]]
    if m["status"] == "pending":
        b["pend"] += 1
        continue
    if m["n"] == 0:
        b["zero"] += 1
    elif m["fav"] is None:
        b["eq"] += 1
    else:
        b["app"] += 1
        b["ok" if m["verdict"] == "ok" else "ko"] += 1
for lg, b in by_league.items():
    rate = f"{100*b['ok']/b['app']:.0f}%" if b["app"] else "—"
    print(f"  {lg:15s} app {b['app']:2d} ok {b['ok']:2d} ko {b['ko']:2d} -> {rate:4s} | eq {b['eq']} zero {b['zero']} attente {b['pend']}")

# favori à domicile / extérieur
for side in ("home", "away"):
    sub = [m for m in applicable if m["fav"] == side]
    o = [m for m in sub if m["verdict"] == "ok"]
    print(f"Favori à {'domicile' if side=='home' else 'extérieur'}: {len(o)}/{len(sub)}")

# par taille d'échantillon
for n in (2, 3, 4):
    sub = [m for m in applicable if m["n"] == n]
    o = [m for m in sub if m["verdict"] == "ok"]
    if sub:
        print(f"Échantillon {n} matchs: {len(o)}/{len(sub)}")

# échecs
print("\nÉCHECS :")
for m in ko:
    print(f"  {m['league']}: {m['home']} {m['score']} {m['away']} (favori {m['fav']})")

print("\nRÉUSSITES avec nul :")
for m in ok:
    if m["res"] == "D":
        print(f"  {m['home']} {m['score']} {m['away']}")

# CSV
with open(os.path.join(OUT_DIR, "bilan_h2h.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Championnat", "Date", "Domicile", "Extérieur", "Score", "Confrontations",
                "Victoires domicile", "Nuls", "Victoires extérieur", "Favori H2H",
                "Statut", "Verdict"])
    for m in MATCHES:
        fav = "" if m["fav"] is None else (m["home"] if m["fav"] == "home" else m["away"])
        statut = "À jouer" if m["status"] == "pending" else ("Aucun historique" if m["n"] == 0 else ("Pas de favori" if not m["fav"] else "Analysé"))
        verdict = {"ok": "Respecté", "ko": "Contredit", None: ""}[m["verdict"]]
        w.writerow([m["league"], m["date"], m["home"], m["away"], m["score"] or "à venir", m["n"],
                    m["hw"], m["dr"], m["aw"], fav, statut, verdict])
print("\nCSV écrit.")
