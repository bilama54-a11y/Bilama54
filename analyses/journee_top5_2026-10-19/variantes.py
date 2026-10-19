# -*- coding: utf-8 -*-
"""Variantes de la règle H2H : que faut-il filtrer pour améliorer le taux ?

Reproduit tous les chiffres de `ameliorer_la_stat.md`.
Usage : python3 variantes.py
"""
import os, sys, math
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from donnees_h2h import MATCHES

for m in MATCHES:
    hw = aw = d = gdh = gda = wh = wa = 0
    for s, th, ta, hs, as_ in m["h2h"]:
        # buts pour/contre du club qui reçoit dans le match du jour
        if th == m["home"]:
            gdh += hs; gda += as_
        else:
            gdh += as_; gda += hs
        if hs > as_:
            w = th
        elif as_ > hs:
            w = ta
        else:
            w = None; d += 1
        weight = 2 if s == "2025-26" else 1
        if w == m["home"]:
            hw += 1; wh += weight
        elif w == m["away"]:
            aw += 1; wa += weight
    m.update(hw=hw, aw=aw, dr=d, n=len(m["h2h"]), gdh=gdh, gda=gda, wh=wh, wa=wa,
             gap=abs(hw - aw))
    m["fav"] = "home" if hw > aw else ("away" if aw > hw else None)
    m["fav_recent"] = None if m["n"] == 0 else ("home" if wh > wa else ("away" if wa > wh else None))
    if m["score"]:
        h, a = map(int, m["score"].split("-"))
        m["res"] = "H" if h > a else ("A" if a > h else "D")
        m["ok"] = ((m["fav"] == "home" and m["res"] in "HD")
                   or (m["fav"] == "away" and m["res"] in "AD"))
        f2 = m["fav_recent"]
        m["ok_recent"] = ((f2 == "home" and m["res"] in "HD")
                          or (f2 == "away" and m["res"] in "AD"))
        m["home1x"] = m["res"] in "HD"
    else:
        m["res"] = None
        m["ok"] = m["ok_recent"] = m["home1x"] = None

played = [m for m in MATCHES if m["score"]]
app = [m for m in played if m["fav"]]


def stat(sub, key="ok"):
    n = len(sub)
    k = sum(1 for m in sub if m[key])
    p = 100 * k / n if n else 0.0
    se = math.sqrt((p / 100) * (1 - p / 100) / n) * 100 if n else 0.0
    return k, n, p, 1.96 * se


def line(label, sub, key="ok"):
    k, n, p, ci = stat(sub, key)
    be = 100 / p if p else float("inf")
    print(f"{label:<42}{k:>3}/{n:<3} {p:5.1f} %   IC95 ±{ci:4.1f}   cote mini {be:4.2f}")


print("=" * 84)
print("1. POINT DE DEPART")
print("=" * 84)
line("règle brute (tous les applicables)", app)
line("témoin : domicile 1X, les mêmes 28 matchs", app, "home1x")
line("témoin : domicile 1X, les 45 matchs joués", played, "home1x")

print()
print("=" * 84)
print("2. FILTRES TESTÉS")
print("=" * 84)
line("favori à domicile", [m for m in app if m["fav"] == "home"])
line("favori à l'extérieur", [m for m in app if m["fav"] == "away"])
line("base de 4 confrontations", [m for m in app if m["n"] == 4])
line("base de 2 confrontations", [m for m in app if m["n"] == 2])
line("écart de victoires ≤ 2", [m for m in app if m["gap"] <= 2])
line("écart de victoires ≥ 3", [m for m in app if m["gap"] >= 3])
line("domicile + écart ≤ 2", [m for m in app if m["fav"] == "home" and m["gap"] <= 2])
line("domicile + écart ≥ 3", [m for m in app if m["fav"] == "home" and m["gap"] >= 3])
line("domicile + base 4", [m for m in app if m["fav"] == "home" and m["n"] == 4])
line("domicile + base 2", [m for m in app if m["fav"] == "home" and m["n"] == 2])
line("hors Serie A", [m for m in app if m["league"] != "Serie A"])

print()
print("=" * 84)
print("3. LE CROISEMENT QUI CASSE TOUT (domicile/extérieur × taille d'échantillon)")
print("=" * 84)
for v in ("home", "away"):
    for s in (2, 4):
        sub = [m for m in app if m["fav"] == v and m["n"] == s]
        k, n, p, _ = stat(sub)
        print(f"  {'domicile' if v == 'home' else 'extérieur':<10} base {s} : {k}/{n} = {p:5.1f} %")

print()
print("=" * 84)
print("4. PONDERATION DE LA SAISON RECENTE (2025-26 comptée double)")
print("=" * 84)
appr = [m for m in played if m["fav_recent"]]
line("favori pondéré", appr, "ok_recent")
chg = [m for m in played if m["n"] and m["fav_recent"] != m["fav"]]
print(f"  paris changés : {len(chg)}")
for m in chg:
    print(f"    {m['home']} – {m['away']} ({m['score']}) : "
          f"{m['fav'] or 'aucun'} → {m['fav_recent'] or 'aucun'}")

print()
print("=" * 84)
print("5. LES TROUS : PEUT-ON LES COMBLER ?")
print("=" * 84)
zero = [m for m in played if m["n"] == 0]
line("sans historique → domicile 1X", zero, "home1x")
eq = [m for m in played if m["n"] > 0 and not m["fav"]]
gd_ok = gd_n = 0
for m in eq:
    pick = "home" if m["gdh"] > m["gda"] else ("away" if m["gda"] > m["gdh"] else None)
    if pick:
        gd_n += 1
        if (pick == "home" and m["res"] in "HD") or (pick == "away" and m["res"] in "AD"):
            gd_ok += 1
print(f"{'égalités → départage par différence de buts':<42}{gd_ok:>3}/{gd_n:<3} "
      f"{100 * gd_ok / gd_n if gd_n else 0:5.1f} %")
print(f"  (sur les {len(eq)} égalités, dont {len(eq) - gd_n} encore à égalité de buts)")

print()
print("=" * 84)
print("6. TOUTES LES ERREURS, PAR PROFIL")
print("=" * 84)
for m in app:
    if not m["ok"]:
        print(f"  {m['league']:<14} {m['home']:>22} {m['score']:>5} {m['away']:<20} "
              f"favori={'dom' if m['fav'] == 'home' else 'ext'} écart={m['gap']} base={m['n']}")
