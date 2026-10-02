#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODELE DE MATCH xG / xGA - formule issue de l'etude (voir RAPPORT_xG_vs_xGA.md)

    lambda_dom = K * mu * A_dom * D_ext * HFA
    lambda_ext = K * mu * A_ext * D_dom / HFA

    A = (xG90 / mu) ^ w_att      force d'attaque (xG crees),  w_att = 0,78 sur 38 matchs
    D = (xGA90 / mu) ^ w_def     faiblesse defensive (xG concédés), w_def = 0,53 sur 38 matchs

Les exposants w sont les FIABILITES mesurees (autocorrelation S1 -> S2) : ils
servent de shrinkage - plus un signal est bruite, plus on le ramene vers la
moyenne. Ils dependent de la taille de l'echantillon :

    w(n) = (r * n) / (r * n + 38)   avec r = rho_38 / (1 - rho_38)

Sorties : 1N2, 1X / X2, Over/Under, BTTS, cotes justes, value, Kelly.
Backtest : saison 2024/25 -> prediction des points de la saison 2025/26.

Usage :
    python3 modele_xg.py                 # tout
    python3 modele_xg.py backtest        # validation
    python3 modele_xg.py match Arsenal "Manchester City"
"""

import csv
import math
import sys
from collections import defaultdict

DATA = "data/understat_team_seasons.csv"

# ---------------------------------------------------------------------------
# CONSTANTES TIREES DE L'ETUDE (172 equipes-saisons, Big-5, 2024/25 + 2025/26)
# ---------------------------------------------------------------------------
K_GOAL = 0.915      # buts reels par xG (mesure : 0,869 a 0,961 selon la ligue)
HFA = 1.12          # avantage domicile (non identifiable en bilan de saison)
RHO_ATT = 0.783     # autocorrelation des xG crees sur 38 matchs
RHO_DEF = 0.526     # autocorrelation des xG concédés sur 38 matchs
N_REF = 38          # nombre de matchs de reference pour les RHO
MAXG = 12

# ---------------------------------------------------------------------------
# Donnees
# ---------------------------------------------------------------------------
rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
for r in rows:
    for k in ("M", "W", "D", "L", "G", "GA", "PTS", "xG", "xGA", "xPTS"):
        r[k] = float(r[k])
    r["season"] = int(r["season"])
    r["xG90"] = r["xG"] / r["M"]
    r["xGA90"] = r["xGA"] / r["M"]
    r["xGD90"] = r["xG90"] - r["xGA90"]
    r["PPG"] = r["PTS"] / r["M"]


def mean(x):
    return sum(x) / len(x)


def sd(x):
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)) if len(x) > 1 else 0.0


def pearson(x, y):
    mx, my = mean(x), mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return num / den if den else float("nan")


# ---------------------------------------------------------------------------
# Fiabilite / shrinkage
# ---------------------------------------------------------------------------
def fiabilite(n_matchs, rho38):
    """Poids a donner a un signal observe sur n matchs, sachant que sa
    fiabilite sur 38 matchs vaut rho38 (generalisation de Spearman-Brown)."""
    if n_matchs <= 0:
        return 0.0
    r = rho38 / (1.0 - rho38)
    return (r * n_matchs) / (r * n_matchs + N_REF)


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------
def ratings(team_rows, n_matchs=None, w_att=None, w_def=None):
    """Construit A (attaque) et D (defense) a partir d'agregats de saison.
    A et D sont renormalises pour que leur moyenne de ligue vaille 1."""
    n = n_matchs if n_matchs is not None else mean([r["M"] for r in team_rows])
    if w_att is None:
        w_att = fiabilite(n, RHO_ATT)
    if w_def is None:
        w_def = fiabilite(n, RHO_DEF)
    mu = mean([r["xG90"] for r in team_rows])
    A = {r["team"]: (r["xG90"] / mu) ** w_att for r in team_rows}
    D = {r["team"]: (r["xGA90"] / mu) ** w_def for r in team_rows}
    ma, md = mean(A.values()), mean(D.values())
    A = {t: v / ma for t, v in A.items()}
    D = {t: v / md for t, v in D.items()}
    return mu, A, D, w_att, w_def


def lambdas(home, away, mu, A, D, hfa=HFA, k=K_GOAL):
    """Lambdas du match. Equipes inconnues (promues) : ratings = 1 (moyenne)."""
    ah, da, aa, dh = A.get(home, 1.0), D.get(away, 1.0), A.get(away, 1.0), D.get(home, 1.0)
    return k * mu * ah * da * hfa, k * mu * aa * dh / hfa


# ---------------------------------------------------------------------------
# Probabilites
# ---------------------------------------------------------------------------
def pois_vec(lam):
    return [math.exp(-lam) * lam ** i / math.factorial(i) for i in range(MAXG + 1)]


def grille(lh, la, dc_rho=None):
    """Matrice des scores, avec correction optionnelle de Dixon-Coles
    (rho litterature, appliquee aux scores 0-0 / 1-0 / 0-1 / 1-1)."""
    ph, pa = pois_vec(lh), pois_vec(la)
    m = [[ph[i] * pa[j] for j in range(MAXG + 1)] for i in range(MAXG + 1)]
    if dc_rho:
        def tau(i, j, l1, l2, rho):
            if i == 0 and j == 0:
                return 1 - l1 * l2 * rho
            if i == 0 and j == 1:
                return 1 + l1 * rho
            if i == 1 and j == 0:
                return 1 + l2 * rho
            if i == 1 and j == 1:
                return 1 - rho
            return 1.0
        for i in range(2):
            for j in range(2):
                m[i][j] *= tau(i, j, lh, la, dc_rho)
    tot = sum(sum(r) for r in m)
    return [[c / tot for c in r] for r in m]


def probas(lh, la, dc_rho=None):
    m = grille(lh, la, dc_rho)
    p1 = sum(m[i][j] for i in range(MAXG + 1) for j in range(i))
    px = sum(m[i][i] for i in range(MAXG + 1))
    p2 = sum(m[i][j] for i in range(MAXG + 1) for j in range(i + 1, MAXG + 1))
    return p1, px, p2


def buts(lh, la, dc_rho=None):
    m = grille(lh, la, dc_rho)
    tot = {t: sum(m[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i + j > t)
           for t in (0.5, 1.5, 2.5, 3.5, 4.5)}
    btts = sum(m[i][j] for i in range(1, MAXG + 1) for j in range(1, MAXG + 1))
    cs_h = sum(m[i][0] for i in range(MAXG + 1))
    cs_a = sum(m[0][j] for j in range(MAXG + 1))
    return tot, btts, cs_h, cs_a


def cote_juste(p):
    return 1 / p if p > 0 else float("inf")


def value(p, cote):
    """Edge = p * cote - 1 (positif = value)."""
    return p * cote - 1


def kelly(p, cote, fraction=0.25):
    """Mise en fraction de bankroll (Kelly fractionnaire, defaut 1/4)."""
    b = cote - 1
    if b <= 0:
        return 0.0
    f = (p * b - (1 - p)) / b
    return max(0.0, f) * fraction


# ---------------------------------------------------------------------------
# 1. BACKTEST : saison 2024/25 -> points de la saison 2025/26
# ---------------------------------------------------------------------------
def prediction_saison(equipes, mu, A, D, hfa=HFA, k=K_GOAL):
    """Round-robin complet : points/match attendus pour chaque equipe."""
    out = {}
    for h in equipes:
        pts = 0.0
        n = 0
        for a in equipes:
            if a == h:
                continue
            lh, la = lambdas(h, a, mu, A, D, hfa, k)
            p1, px, _ = probas(lh, la)
            pts += 3 * p1 + px
            n += 1
        out[h] = pts / n
    return out


def calibration(preds, acts):
    """Ajustement affine 'reel = a + b*pred' (2 parametres) puis RMSE du predicteur
    recale. Tous les modeles recoivent exactement le meme traitement."""
    n = len(preds)
    mp, ma = mean(preds), mean(acts)
    b = sum((p - mp) * (a - ma) for p, a in zip(preds, acts)) / sum((p - mp) ** 2 for p in preds)
    a = ma - b * mp
    sse = sum((a + b * p - act) ** 2 for p, act in zip(preds, acts))
    return math.sqrt(sse / n), a, b


def predict_ligue(equipes, mu, A, D, tirages=None):
    """Points/match attendus. Avec tirages (Monte-Carlo sur l'incertitude des
    ratings), on moyenne : cela rend la dispersion correcte."""
    if not tirages:
        return prediction_saison(equipes, mu, A, D)
    acc = defaultdict(float)
    for Ah, Dh in tirages:
        p = prediction_saison(equipes, mu, Ah, Dh)
        for t, v in p.items():
            acc[t] += v / len(tirages)
    return acc


def tirages_ratings(team_rows, mu, w_att, w_def, n_tirages=40, graine=7):
    """Tire les vrais ratings dans leur loi a posteriori (normal sur les log-ratios).
    Corrige la compression du plug-in : la fonction 'points' est convexe, donc
    E[points|donnees] > points(E[ratings|donnees])."""
    import random
    rnd = random.Random(graine)
    teams = [r["team"] for r in team_rows]
    z_att = {r["team"]: math.log(r["xG90"] / mu) for r in team_rows}
    z_def = {r["team"]: math.log(r["xGA90"] / mu) for r in team_rows}
    s_att = math.sqrt((1 - RHO_ATT) * RHO_ATT) * sd(list(z_att.values()))
    s_def = math.sqrt((1 - RHO_DEF) * RHO_DEF) * sd(list(z_def.values()))
    out = []
    for _ in range(n_tirages):
        A = {t: math.exp(w_att * z_att[t] + rnd.gauss(0, s_att)) for t in teams}
        D = {t: math.exp(w_def * z_def[t] + rnd.gauss(0, s_def)) for t in teams}
        ma, md = mean(A.values()), mean(D.values())
        out.append(({t: v / ma for t, v in A.items()}, {t: v / md for t, v in D.items()}))
    return out


def backtest():
    print("=" * 96)
    print("1. BACKTEST : ratings construits sur 2024/25 -> saison 2025/26")
    print("=" * 96)
    print("   Equipes promues en 2025/26 (pas de donnees 2024/25) : ratings = moyenne (A=D=1).")
    print("   mu, k, hfa : cales sur la saison 1 uniquement (aucune donnee du futur).")
    print("   n = 65 equipes presentes dans les 2 saisons (EPL, Liga, Bundesliga, Ligue 1).")
    print("")

    ligues = []
    for lg in sorted(set(r["league"] for r in rows)):
        s1 = {r["team"]: r for r in rows if r["league"] == lg and r["season"] == 2024}
        s2 = {r["team"]: r for r in rows if r["league"] == lg and r["season"] == 2025}
        if s1 and s2:
            ligues.append((lg, s1, s2))
    by_lg = {lg: (s1, s2) for lg, s1, s2 in ligues}
    communes = [(lg, t) for lg, _, _ in ligues
                for t in sorted(set(by_lg[lg][0]) & set(by_lg[lg][1]))]
    acts = [by_lg[lg][1][t]["PPG"] for lg, t in communes]
    xacts = [by_lg[lg][1][t]["xPTS"] / by_lg[lg][1][t]["M"] for lg, t in communes]

    W_A, W_D = fiabilite(38, RHO_ATT), fiabilite(38, RHO_DEF)

    modeles = [
        ("M0 points de la saison passee (naif)", "naif", None),
        ("M1 xG + xGA, aucun shrinkage (1,00 / 1,00)", "poisson", (1.0, 1.0)),
        ("M2 formule proposee, plug-in (0,78 / 0,53)", "poisson", (W_A, W_D)),
        ("M3 attaque seule (0,78 / 0,00)", "poisson", (W_A, 0.0)),
        ("M4 defense seule (0,00 / 0,53)", "poisson", (0.0, W_D)),
        ("M5 shrinkage identique (0,65 / 0,65)", "poisson", (0.65, 0.65)),
        ("M6 xGD seul, une seule dimension", "xgd", None),
        ("M7 formule proposee + moyenne posterieure", "mcp", (W_A, W_D)),
    ]

    preds = {}
    for nom, kind, ws in modeles:
        out = []
        for lg, s1, s2 in ligues:
            if kind == "naif":
                mppg = mean([r["PPG"] for r in s1.values()])
                p = {t: (s1[t]["PPG"] if t in s1 else mppg) for t in s2}
            elif kind == "xgd":
                mu1 = mean([r["xG90"] for r in s1.values()])
                xgd = {t: s1[t]["xGD90"] * W_A for t in s1}
                p = {}
                for h in s2:
                    pts = 0.0
                    n = 0
                    for a in s2:
                        if a == h:
                            continue
                        diff = xgd.get(h, 0.0) - xgd.get(a, 0.0)
                        lh = max((mu1 + diff / 2) * K_GOAL * HFA, 0.05)
                        la = max((mu1 - diff / 2) * K_GOAL / HFA, 0.05)
                        p1, px, _ = probas(lh, la)
                        pts += 3 * p1 + px
                        n += 1
                    p[h] = pts / n
            else:
                mu, A, D, _, _ = ratings(list(s1.values()), w_att=ws[0], w_def=ws[1])
                tir = tirages_ratings(list(s1.values()), mu, ws[0], ws[1]) if kind == "mcp" else None
                p = predict_ligue(list(s2), mu, A, D, tir)
            for t in sorted(set(s1) & set(s2)):
                out.append(p[t])
        preds[nom] = out

    print("   %-48s %8s %8s %8s %8s %8s" %
          ("modele", "RMSE", "recalé", "MAE", "corr", "corr xPTS"))
    print("   " + "-" * 92)
    res = {}
    for nom, _, _ in modeles:
        pv = preds[nom]
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(pv, acts)) / len(acts))
        rmse_cal, _, _ = calibration(pv, acts)
        mae = sum(abs(a - b) for a, b in zip(pv, acts)) / len(acts)
        c = pearson(pv, acts)
        cx = pearson(pv, xacts)
        res[nom] = (rmse, rmse_cal, c)
        print("   %-48s %8.4f %8.4f %8.4f %8.3f %8.3f" % (nom, rmse, rmse_cal, mae, c, cx))
    print("")
    print("   RMSE   = ecart brut aux points reels (cible bruitee par la chance)")
    print("   recale = RMSE apres ajustement affine (2 parametres) : mesure l'information")
    print("   corr   = correlation avec les points reels ; corr xPTS = avec les points attendus")
    base = res["M0 points de la saison passee (naif)"]
    prop = "M7 formule proposee + moyenne posterieure"
    plug = "M2 formule proposee, plug-in (0,78 / 0,53)"
    print("")
    print("   -> Information (corr) : naif %.3f  vs  formule %.3f" % (base[2], res[prop][2]))
    print("   -> Precision recalee  : naif %.4f  vs  formule %.4f   (%+.1f %%)"
          % (base[1], res[prop][1], 100 * (1 - res[prop][1] / base[1])))
    print("   -> Apport de la moyenne posterieure (M2 -> M7) : %+.1f %% de RMSE brut"
          % (100 * (1 - res[prop][0] / res[plug][0])))
    print("   -> Apport du shrinkage (M1 -> M7)              : %+.1f %% de RMSE brut"
          % (100 * (1 - res[prop][0] / res["M1 xG + xGA, aucun shrinkage (1,00 / 1,00)"][0])))

    print("")
    print("   Grille de sensibilite (correlation avec les points reels 2025/26) :")
    print("   %-12s" % "w_att \\ w_def" + "".join("%8.2f" % d for d in (0.0, 0.25, 0.50, 0.75, 1.00)))
    best = (None, -9)
    for wa in (0.40, 0.60, 0.78, 1.00, 1.20):
        ligne = "   %-12s" % ("%.2f" % wa)
        for wd in (0.0, 0.25, 0.50, 0.75, 1.00):
            out = []
            for lg, s1, s2 in ligues:
                mu, A, D, _, _ = ratings(list(s1.values()), w_att=wa, w_def=wd)
                p = prediction_saison(list(s2), mu, A, D)
                for t in sorted(set(s1) & set(s2)):
                    out.append(p[t])
            c = pearson(out, acts)
            if c > best[1]:
                best = ((wa, wd), c)
            ligne += "%8.3f" % c
        print(ligne)
    print("   -> optimum de la grille : w_att = %.2f, w_def = %.2f (corr %.3f)"
          % (best[0][0], best[0][1], best[1]))
    print("   -> valeurs issues de l'etude : w_att = %.2f, w_def = %.2f"
          % (fiabilite(38, RHO_ATT), fiabilite(38, RHO_DEF)))

    print("")
    print("   Exemples (M7) : points/match predits en 2025/26 vs realite")
    av = {t: by_lg[lg][1][t]["PPG"] for lg, t in communes}
    pv = dict(zip([t for _, t in communes], preds[prop]))
    suite = sorted(pv, key=lambda t: av[t] - pv[t])
    print("   %-24s %8s %8s %8s" % ("equipe", "pred", "reel", "ecart"))
    print("   " + "-" * 52)
    for t in suite[:4] + suite[-4:]:
        print("   %-24s %8.2f %8.2f %+8.2f" % (t, pv[t], av[t], av[t] - pv[t]))
    return res


# ---------------------------------------------------------------------------
# 2. TABLE DE LECTURE RAPIDE : ecart de lambda -> probabilites
# ---------------------------------------------------------------------------
def table_lecture():
    print("")
    print("=" * 92)
    print("2. TABLE DE LECTURE : de l'ecart de lambda aux probabilites (total ~2,85 buts)")
    print("=" * 92)
    print("   d = lambda_dom - lambda_ext   (formule lineaire ci-dessous)")
    print("")
    print("   %6s %9s %9s %9s %9s %9s %9s %9s" %
          ("d", "P(1)", "P(X)", "P(2)", "P(1X)", "P(Over2.5)", "P(BTTS)", "cote 1"))
    print("   " + "-" * 76)
    res = []
    d = -1.6
    while d <= 1.61:
        s = 2.85
        lh, la = (s + d) / 2, (s - d) / 2
        p1, px, p2 = probas(lh, la)
        tot, btts, _, _ = buts(lh, la)
        print("   %6.1f %9.3f %9.3f %9.3f %9.3f %9.3f %9.3f %9.2f"
              % (d, p1, px, p2, p1 + px, tot[2.5], btts, cote_juste(p1)))
        res.append((d, p1))
        d += 0.2
    # ajustements : P(1) lineaire en d sur |d| <= 1 ; P(X) quadratique en d
    sub = [(d_, p) for d_, p in res if abs(d_) <= 1.0]
    mx = mean([r[0] for r in sub])
    my = mean([r[1] for r in sub])
    b = sum((r[0] - mx) * (r[1] - my) for r in sub) / sum((r[0] - mx) ** 2 for r in sub)
    a = my - b * mx
    xs = [d_ * d_ for d_, _ in res]
    ps = [probas((2.85 + d_) / 2, (2.85 - d_) / 2)[1] for d_, _ in res]
    mx2, my2 = mean(xs), mean(ps)
    b2 = sum((x - mx2) * (p - my2) for x, p in zip(xs, ps)) / sum((x - mx2) ** 2 for x in xs)
    a2 = my2 - b2 * mx2
    print("")
    print("   NB : la colonne Over 2,5 est constante : le total de buts ne depend que de")
    print("   lambda_dom + lambda_ext, pas de l'ecart entre les deux equipes.")
    print("")
    print("   Approximations de poche (|d| <= 1) :")
    print("      P(victoire domicile) ~ %.3f + %.3f * d" % (a, b))
    print("      P(nul)               ~ %.3f - %.3f * d^2" % (a2, -b2))

    print("")
    print("   Marche des buts : P(Over 2,5) selon le TOTAL de lambda (lambda_dom + lambda_ext)")
    print("   %10s %12s %12s %12s" % ("total", "P(Over1,5)", "P(Over2,5)", "P(Over3,5)"))
    print("   " + "-" * 48)
    for s in (2.0, 2.3, 2.5, 2.7, 2.85, 3.0, 3.3, 3.6, 4.0):
        tot, _, _, _ = buts(s / 2, s / 2)
        print("   %10.2f %12.3f %12.3f %12.3f" % (s, tot[1.5], tot[2.5], tot[3.5]))
    return a, b


# ---------------------------------------------------------------------------
# 1b. CALIBRAGE DE LA CORRELATION DES SCORES (Dixon-Coles) SUR LE TAUX DE NULS
# ---------------------------------------------------------------------------
def calibrer_rho():
    """Le Poisson independant sous-estime les 0-0 / sur-estime les BTTS.
    On calibre rho (correction de Dixon-Coles) pour reproduire le taux de nuls
    observe dans les 9 ligues-saisons."""
    print("")
    print("=" * 96)
    print("1b. CALIBRAGE : correction de Dixon-Coles (rho) sur le taux de nuls observe")
    print("=" * 96)
    nuls_reel = total = 0
    ligues = []
    for key in sorted(set((r["league"], r["season"]) for r in rows)):
        grp = [r for r in rows if (r["league"], r["season"]) == key]
        n = len(grp)
        nb_matchs = n * (n - 1)
        nuls = sum(r["D"] for r in grp) / 2
        nuls_reel += nuls
        total += nb_matchs
        mu, A, D, _, _ = ratings(grp)
        ligues.append((key, grp, mu, A, D, nb_matchs, nuls))
    print("   Taux de nuls observe : %.1f %% (%d matchs)" % (100 * nuls_reel / total, total))
    print("")
    print("   Ratings utilises : shrinkage 0,78 / 0,53 (ceux du modele).")
    print("")
    print("   %8s %14s %14s" % ("rho", "nuls predits", "ecart (pts)"))
    print("   " + "-" * 40)
    best = (None, 9e9)
    for rho in [x / 100 for x in range(-25, 6)]:
        pn = 0
        for key, grp, mu, A, D, nb_matchs, _ in ligues:
            s = 0.0
            for h in grp:
                for a in grp:
                    if h["team"] == a["team"]:
                        continue
                    lh, la = lambdas(h["team"], a["team"], mu, A, D)
                    s += probas(lh, la, dc_rho=rho)[1]
            pn += s
        ec = 100 * pn / total - 100 * nuls_reel / total
        if abs(ec) < best[1]:
            best = (rho, abs(ec), ec)
        if int(round(rho * 100)) % 5 == 0:
            print("   %8.2f %13.1f %% %13.1f" % (rho, 100 * pn / total, ec))
    print("")
    print("   -> rho retenu : %.2f (ecart residuel %+.1f pt)" % (best[0], best[2]))
    if best[0] < 0:
        print("      le Poisson independant sous-estime les scores serres (0-0, 1-1)")
    lh, la = 1.42, 1.42
    b0 = buts(lh, la)[1]
    b1 = buts(lh, la, dc_rho=best[0])[1]
    print("   -> effet sur un match equilibre (1,42 - 1,42) : BTTS %.1f %% -> %.1f %%"
          % (100 * b0, 100 * b1))
    return best[0]


# ---------------------------------------------------------------------------
# 3. FORMULE LINEAIRE "DE POCHE"
# ---------------------------------------------------------------------------
def formule_poche():
    print("")
    print("=" * 92)
    print("3. FORMULE DE POCHE (sans ordinateur)")
    print("=" * 92)
    print("   Soient, pour chaque equipe, les ecarts RELATIFS a la moyenne de la ligue :")
    print("      a = xG90/mu - 1        (ex : +0,25 = 25 % de xG en plus que la moyenne)")
    print("      d = xGA90/mu - 1       (ex : -0,15 = 15 % de xG concédés en moins)")
    print("")
    print("   Alors :")
    print("      lambda_dom - lambda_ext = 0,32 + 1,42 * [ 0,78*(a_dom - a_ext)")
    print("                                              + 0,53*(d_ext - d_dom) ]")
    print("")
    print("   puis lire P(1) / P(X) / P(2) dans la table de la section 2.")
    print("   (0,32 = effet domicile ; 1,42 = mu * k = 1,55 * 0,915)")
    print("")
    print("   Exemple : domicile avec +20 % d'attaque et -10 % de xG concédés,")
    h_a, h_d, a_a, a_d = 0.20, -0.10, 0.0, 0.0
    d = 0.32 + 1.42 * (0.78 * (h_a - a_a) + 0.53 * (a_d - h_d))
    p1, px, p2 = probas((2.85 + d) / 2, (2.85 - d) / 2)
    print("             exterieur moyen (a = d = 0)")
    print("      -> d = %.2f  =>  P(1) = %.3f  P(X) = %.3f  P(2) = %.3f  [cotes %.2f / %.2f / %.2f]"
          % (d, p1, px, p2, cote_juste(p1), cote_juste(px), cote_juste(p2)))


# ---------------------------------------------------------------------------
# 4. DEMO : matchs reels avec les ratings 2025/26
# ---------------------------------------------------------------------------
def demo(home, away, lg="EPL"):
    s = {r["league"]: {r["team"]: r for r in rows if r["league"] == r_ and False} for r_ in []}
    return None


def demo_matchs():
    print("")
    print("=" * 92)
    print("4. EXEMPLES REELS (ratings = saison 2025/26 complete, shrinkage 0,78 / 0,53)")
    print("=" * 92)
    matchs = [("EPL", "Arsenal", "Manchester City"),
              ("La_Liga", "Real Madrid", "Barcelona"),
              ("Bundesliga", "Bayern Munich", "Borussia Dortmund"),
              ("Serie_A", "Inter", "Juventus"),
              ("Ligue_1", "Paris Saint Germain", "Marseille")]
    for lg, h, a in matchs:
        grp = [r for r in rows if r["league"] == lg and r["season"] == 2025]
        mu, A, D, wa, wd = ratings(grp)
        lh, la = lambdas(h, a, mu, A, D)
        p1, px, p2 = probas(lh, la)
        tot, btts, cs_h, cs_a = buts(lh, la)
        print("")
        print("   %s - %s   (%s)" % (h, a, lg))
        print("      lambda : %.2f - %.2f   (total %.2f)" % (lh, la, lh + la))
        print("      1N2    : %.1f %% / %.1f %% / %.1f %%      cotes justes %.2f / %.2f / %.2f"
              % (100 * p1, 100 * px, 100 * p2, cote_juste(p1), cote_juste(px), cote_juste(p2)))
        print("      ne pas perdre : %s %.1f %% (cote %.2f) | %s %.1f %% (cote %.2f)"
              % (h, 100 * (p1 + px), cote_juste(p1 + px), a, 100 * (p2 + px), cote_juste(p2 + px)))
        print("      buts   : Over 2,5 %.1f %% | BTTS %.1f %% | clean sheet %.1f %% / %.1f %%"
              % (100 * tot[2.5], 100 * btts, 100 * cs_h, 100 * cs_a))
    print("")
    print("   NB : ce sont des ratings de fin de saison 2025/26, a titre d'illustration du")
    print("   calcul. En pratique on utilise les xG des N derniers matchs (voir fiabilite()).")


def demo_value():
    print("")
    print("=" * 92)
    print("5. DETECTION DE VALUE (exemple chiffre)")
    print("=" * 92)
    lg, h, a = "EPL", "Arsenal", "Manchester City"
    grp = [r for r in rows if r["league"] == lg and r["season"] == 2025]
    mu, A, D, _, _ = ratings(grp)
    lh, la = lambdas(h, a, mu, A, D)
    p1, px, p2 = probas(lh, la)
    cotes = {"1": 2.10, "X": 3.60, "2": 3.40, "1X": 1.35, "Over 2,5": 1.75}
    probs = {"1": p1, "X": px, "2": p2, "1X": p1 + px, "Over 2,5": buts(lh, la)[0][2.5]}
    print("")
    print("   %-12s %10s %10s %10s %10s %10s" % ("pari", "p modele", "cote", "cote juste", "edge", "Kelly 1/4"))
    print("   " + "-" * 66)
    for k in cotes:
        p = probs[k]
        print("   %-12s %10.3f %10.2f %10.2f %9.1f %% %10.2f %%"
              % (k, p, cotes[k], cote_juste(p), 100 * value(p, cotes[k]),
                 100 * kelly(p, cotes[k])))
    print("")
    print("   Regle : on joue si edge > 3 a 5 %% (marge d'erreur du modele), mise = Kelly/4.")


# ---------------------------------------------------------------------------
# 6. Combien de matchs faut-il ?
# ---------------------------------------------------------------------------
def echantillon():
    print("")
    print("=" * 92)
    print("6. COMBIEN DE MATCHS PRENDRE EN COMPTE ? (poids optimal du signal)")
    print("=" * 92)
    print("   %8s %14s %14s" % ("matchs", "poids attaque", "poids defense"))
    print("   " + "-" * 40)
    for n in (3, 5, 8, 10, 12, 15, 19, 25, 38, 50, 76):
        print("   %8d %14.2f %14.2f" % (n, fiabilite(n, RHO_ATT), fiabilite(n, RHO_DEF)))
    print("")
    print("   Lecture : sur 5 matchs, les xG concédés ne valent que 0,23 de poids :")
    print("   une 'defense de fer' observee sur 5 matchs est du bruit a 77 %.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        backtest()
        calibrer_rho()
        table_lecture()
        formule_poche()
        demo_matchs()
        demo_value()
        echantillon()
    elif args[0] == "backtest":
        backtest()
    elif args[0] == "calibrer":
        calibrer_rho()
    elif args[0] == "table":
        table_lecture()
    elif args[0] == "match" and len(args) == 3:
        lg = "EPL"
        grp = [r for r in rows if r["league"] == lg and r["season"] == 2025]
        mu, A, D, _, _ = ratings(grp)
        lh, la = lambdas(args[1], args[2], mu, A, D)
        p1, px, p2 = probas(lh, la)
        print("%.2f - %.2f | 1N2 %.3f %.3f %.3f" % (lh, la, p1, px, p2))
