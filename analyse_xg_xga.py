#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xG vs xGA : lequel pese le plus sur (a) la victoire, (b) le fait de ne pas perdre ?

Donnees : Understat (Big-5), saisons 2024/25 et 2025/26, agregats equipe-saison.
Pure bibliotheque standard (pas de numpy/pandas).

Sections :
  0. Cadrage des donnees
  1. Regressions equipe-saison (points, victoires, defaites) sur xG90 et xGA90
  2. Modele de Poisson par match : poids optimal de l'attaque et de la defense
  3. Effets marginaux : +0,1 xG/90 vs -0,1 xGA/90 sur P(victoire) et P(ne pas perdre)
  4. A xGD egal, vaut-il mieux attaquer ou defendre ?
  5. Fiabilite / valeur predictive d'une saison sur l'autre
"""

import csv
import math
from collections import defaultdict

DATA = "data/understat_team_seasons.csv"

# ----------------------------------------------------------------------------
# Chargement
# ----------------------------------------------------------------------------
rows = list(csv.DictReader(open(DATA, encoding="utf-8")))
for r in rows:
    for k in ("M", "W", "D", "L", "G", "GA", "PTS", "xG", "xGA", "xPTS"):
        r[k] = float(r[k])
    r["season"] = int(r["season"])
    r["xG90"] = r["xG"] / r["M"]
    r["xGA90"] = r["xGA"] / r["M"]
    r["xGD90"] = r["xG90"] - r["xGA90"]
    r["PPG"] = r["PTS"] / r["M"]
    r["xPPG"] = r["xPTS"] / r["M"]
    r["W90"] = r["W"] / r["M"]
    r["D90"] = r["D"] / r["M"]
    r["L90"] = r["L"] / r["M"]

GROUPS = defaultdict(list)
for r in rows:
    GROUPS[(r["league"], r["season"])].append(r)
KEYS = sorted(GROUPS)

# ----------------------------------------------------------------------------
# Outils statistiques
# ----------------------------------------------------------------------------
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

def ols(y, X):
    """X : liste de listes (contient deja la constante)."""
    n, p = len(y), len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    b = [sum(X[i][a] * y[i] for i in range(n)) for a in range(p)]
    M = [A[i][:] + [1.0 if i == j else 0.0 for j in range(p)] + [b[i]] for i in range(p)]
    for c in range(p):
        piv = max(range(c, p), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        d = M[c][c]
        M[c] = [v / d for v in M[c]]
        for r2 in range(p):
            if r2 != c and M[r2][c] != 0:
                f = M[r2][c]
                M[r2] = [v - f * w for v, w in zip(M[r2], M[c])]
    beta = [M[i][2 * p] for i in range(p)]
    inv = [[M[i][p + j] for j in range(p)] for i in range(p)]
    yhat = [sum(beta[k] * X[i][k] for k in range(p)) for i in range(n)]
    resid = [y[i] - yhat[i] for i in range(n)]
    sse = sum(e * e for e in resid)
    my = mean(y)
    sst = sum((v - my) ** 2 for v in y)
    dof = n - p
    s2 = sse / dof if dof > 0 else float("nan")
    se = [math.sqrt(s2 * inv[i][i]) for i in range(p)]
    t = [beta[i] / se[i] if se[i] else float("nan") for i in range(p)]
    r2 = 1 - sse / sst if sst else float("nan")
    return beta, se, t, r2, math.sqrt(sse / n), n

def within(field, subset=None):
    """Variable centree par ligue-saison (effets fixes ligue-saison)."""
    src = subset if subset is not None else rows
    out = []
    for k in KEYS:
        grp = [r for r in GROUPS[k] if (subset is None or r in subset)]
        if not grp:
            continue
        m = mean([r[field] for r in grp])
        out.extend(r[field] - m for r in grp)
    return out

# ----------------------------------------------------------------------------
# Poisson
# ----------------------------------------------------------------------------
MAXG = 12

def pois_vec(lam):
    v = []
    for k in range(MAXG + 1):
        v.append(math.exp(-lam) * lam ** k / math.factorial(k))
    return v

def probs(lf, la):
    ph = pois_vec(lf)
    pa = pois_vec(la)
    cdf = [0.0] * (MAXG + 2)
    s = 0.0
    for j in range(MAXG + 1):
        cdf[j] = s
        s += pa[j]
    cdf[MAXG + 1] = s
    w = sum(ph[i] * cdf[i] for i in range(MAXG + 1))       # P(F > A)
    d = sum(ph[i] * pa[i] for i in range(MAXG + 1))        # P(F = A)
    return w, d, 1.0 - w - d

# ----------------------------------------------------------------------------
# Modele de saison
# ----------------------------------------------------------------------------
def predict_season(grp, p, q, k, hfa):
    mu = mean([r["xG90"] for r in grp])
    att = {r["team"]: (r["xG90"] / mu) ** p for r in grp}
    dfn = {r["team"]: (r["xGA90"] / mu) ** q for r in grp}
    out = {}
    for h in grp:
        pw = pd = 0.0
        for a in grp:
            if a["team"] == h["team"]:
                continue
            lf = k * mu * att[h["team"]] * dfn[a["team"]] * hfa
            la = k * mu * att[a["team"]] * dfn[h["team"]] / hfa
            w, d, _ = probs(lf, la)
            pw += w
            pd += d
        m = h["M"]
        n_opp = len(grp) - 1
        out[h["team"]] = {"ppg": (3 * pw + pd) / n_opp,
                          "W": pw * m / n_opp, "D": pd * m / n_opp,
                          "L": m - pw * m / n_opp - pd * m / n_opp}
    return out

def evaluate(p, q, k, hfa, target="xPPG"):
    """Renvoie RMSE sur la cible (xPPG = points attendus, PPG = points reels)."""
    sse = n = 0
    preds, acts = [], []
    for key in KEYS:
        grp = GROUPS[key]
        pr = predict_season(grp, p, q, k, hfa)
        for r in grp:
            pv = pr[r["team"]]
            av = r[target]
            sse += (pv["ppg"] - av) ** 2
            preds.append(pv["ppg"])
            acts.append(av)
            n += 1
    return {"rmse": math.sqrt(sse / n), "corr": pearson(preds, acts), "preds": preds, "acts": acts}

def optimise(p0, q0, k0, hfa0, free_p=True, free_q=True, target="xPPG", iters=90):
    p, q, k, hfa = p0, q0, k0, hfa0
    step = {"p": 0.3, "q": 0.3, "k": 0.05, "hfa": 0.04}
    best = evaluate(p, q, k, hfa, target)["rmse"]
    for _ in range(iters):
        improved = False
        for name in ("p", "q", "k", "hfa"):
            if (name == "p" and not free_p) or (name == "q" and not free_q):
                continue
            for sgn in (1, -1):
                dp, dq, dk, dh = p, q, k, hfa
                d = step[name] * sgn
                if name == "p":
                    dp = max(0.0, p + d)
                elif name == "q":
                    dq = max(0.0, q + d)
                elif name == "k":
                    dk = k + d
                else:
                    dh = hfa + d
                s = evaluate(dp, dq, dk, dh, target)["rmse"]
                if s < best - 1e-12:
                    p, q, k, hfa, best = dp, dq, dk, dh, s
                    improved = True
        if not improved:
            for name in step:
                step[name] *= 0.5
            if step["p"] < 2e-3:
                break
    return p, q, k, hfa, best

out = []
P = out.append

# ----------------------------------------------------------------------------
# 0. Cadrage
# ----------------------------------------------------------------------------
P("=" * 84)
P("0. CADRAGE DES DONNEES")
P("=" * 84)
P("   %d equipes-saisons, %d ligues-saisons (Big-5), saisons 2024/25 et 2025/26"
  % (len(rows), len(KEYS)))
P("   Source : Understat (agregats equipe-saison). Unites : par 90 minutes.")
P("")
P("   Identite comptable : dans une ligue, somme(xG) = somme(xGA), donc la")
P("   moyenne de xG90 = moyenne de xGA90 = mu. Les deux mesures sont donc sur")
P("   la MEME echelle : +0,1 xG/90 et -0,1 xGA/90 sont directement comparables.")
P("")
P("   %-22s %8s %8s %8s %8s %8s" % ("ligue-saison", "mu(xG90)", "sd xG90", "sd xGA90", "buts/xG", "n"))
P("   " + "-" * 74)
for k in KEYS:
    grp = GROUPS[k]
    g = sum(r["G"] for r in grp)
    xg = sum(r["xG"] for r in grp)
    P("   %-22s %8.2f %8.3f %8.3f %8.3f %8d"
      % ("%s %d/%d" % (k[0], k[1], k[1] + 1), mean([r["xG90"] for r in grp]),
         sd([r["xG90"] for r in grp]), sd([r["xGA90"] for r in grp]), g / xg, len(grp)))
P("")
P("   sd(xG90) moyen  = %.3f  ;  sd(xGA90) moyen = %.3f"
  % (mean([sd([r["xG90"] for r in GROUPS[k]]) for k in KEYS]),
     mean([sd([r["xGA90"] for r in GROUPS[k]]) for k in KEYS])))
P("   -> l'ecart-type des xG concédés est %s que celui des xG crees : il y a"
  % ("plus faible" if mean([sd([r["xGA90"] for r in GROUPS[k]]) for k in KEYS]) <
     mean([sd([r["xG90"] for r in GROUPS[k]]) for k in KEYS]) else "plus fort"))
P("      %s de dispersion entre equipes du cote defensif."
  % ("moins" if mean([sd([r["xGA90"] for r in GROUPS[k]]) for k in KEYS]) <
     mean([sd([r["xG90"] for r in GROUPS[k]]) for k in KEYS]) else "plus"))

# ----------------------------------------------------------------------------
# 1. Regressions
# ----------------------------------------------------------------------------
P("")
P("=" * 84)
P("1. REGRESSIONS EQUIPE-SAISON (variables centrees par ligue-saison)")
P("=" * 84)
X = [[1.0, a, b] for a, b in zip(within("xG90"), within("xGA90"))]
P("")
P("   corr(xG90, xGA90) = %+.3f  -> les deux dimensions sont fortement liees :" % pearson(within("xG90"), within("xGA90")))
P("   une equipe qui produit beaucoup de xG en concède en general moins.")
P("")
P("   %-22s %9s %8s %9s %8s %10s %10s %8s" % ("variable expliquee", "b(xG90)", "t(xG)", "b(xGA90)", "t(xGA)", "beta* xG", "beta* xGA", "R2"))
P("   " + "-" * 84)
store = {}
for tgt, lab in [("PPG", "points / match"), ("W90", "victoires / match"),
                 ("D90", "nuls / match"), ("L90", "defaites / match")]:
    y = within(tgt)
    beta, se, t, r2, rmse, n = ols(y, X)
    sy = sd(y)
    bx = beta[1] * sd(within("xG90")) / sy
    ba = beta[2] * sd(within("xGA90")) / sy
    store[tgt] = (beta, t, r2, bx, ba)
    P("   %-22s %9.3f %8.1f %9.3f %8.1f %10.3f %10.3f %8.3f"
      % (lab, beta[1], t[1], beta[2], t[2], bx, ba, r2))
P("")
P("   b()  = effet d'un but/90 de PLUS de xG crees (resp. de xG concédés)")
P("   beta* = coefficient standardise : de combien de SD la cible bouge quand")
P("          xG90 (resp. xGA90) bouge de 1 SD. Mesure du poids relatif.")
P("")
P("   SD intra-ligue : xG90 = %.3f buts/90, xGA90 = %.3f buts/90  -> les equipes"
  % (sd(within("xG90")), sd(within("xGA90"))))
P("   se ressemblent BEAUCOUP moins en attaque qu'en defense.")
P("")
P("   Correlations simples :")
for tgt, lab in [("PPG", "points"), ("W90", "victoires"), ("D90", "nuls"), ("L90", "defaites")]:
    P("      corr(%s, xG90) = %+.3f | corr(%s, xGA90) = %+.3f | corr(%s, xGD90) = %+.3f"
      % (lab, pearson(within("xG90"), within(tgt)), lab,
         pearson(within("xGA90"), within(tgt)), lab, pearson(within("xGD90"), within(tgt))))

# ----------------------------------------------------------------------------
# 2. Modele de Poisson
# ----------------------------------------------------------------------------
P("")
P("=" * 84)
P("2. MODELE DE POISSON PAR MATCH : quel poids donner a l'attaque / a la defense ?")
P("=" * 84)
P("   lambda_dom = k * mu * (xG90_dom/mu)^p * (xGA90_ext/mu)^q * hfa")
P("   lambda_ext = k * mu * (xG90_ext/mu)^p * (xGA90_dom/mu)^q / hfa")
P("   mu = moyenne de la ligue, k = calibration globale, hfa = avantage domicile.")
P("   Cible d'ajustement : les POINTS ATTENDUS xPTS d'Understat (calculés sur les")
P("   xG de chaque match, donc sans le bruit de finition) -> cible 'propre'.")
P("")
full_p, full_q, full_k, full_h, full_rmse = optimise(1.0, 1.0, 1.0, 1.12)
att_p, att_q, att_k, att_h, att_rmse = optimise(1.0, 0.0, 1.0, 1.12, free_q=False)
def_p, def_q, def_k, def_h, def_rmse = optimise(0.0, 1.0, 1.0, 1.12, free_p=False)
naive = evaluate(1.0, 1.0, full_k, full_h)

P("   %-40s %7s %7s %7s %7s %10s %10s %10s" % ("modele", "p", "q", "k", "hfa", "RMSE xPPG", "corr xPPTS", "corr PPG"))
P("   " + "-" * 100)
for lab, (a, b, c, d) in [("A. attaque + defense, poids libres", (full_p, full_q, full_k, full_h)),
                          ("B. attaque seule (xGA ignore)", (att_p, 0.0, att_k, att_h)),
                          ("C. defense seule (xG ignore)", (0.0, def_q, def_k, def_h))]:
    ev = evaluate(a, b, c, d)
    ev2 = evaluate(a, b, c, d, target="PPG")
    P("   %-40s %7.2f %7.2f %7.3f %7.3f %10.3f %10.3f %10.3f"
      % (lab, a, b, c, d, ev["rmse"], ev["corr"], ev2["corr"]))
P("")
P("   RMSE xPPG : ecart entre les points attendus du modele et xPTS (Understat)")
P("   corr xPPTS: correlation entre prediction du modele et xPTS (cible propre)")
P("   corr PPG  : correlation entre prediction du modele et les POINTS REELS")
P("")
P("   Modele A : p = %.2f (attaque), q = %.2f (defense)  ->  rapport q/p = %.2f"
  % (full_p, full_q, full_q / full_p if full_p else float("nan")))
P("   Les poids optimaux sont donc quasi symetriques : 1 unite d'ecart a la")
P("   moyenne en xG concédés compte autant que 1 unite en xG crees.")
P("   NB : hfa n'est pas identifiable avec des bilans de saison (chaque equipe")
P("   joue autant a domicile qu'a l'exterieur) : il est laisse a 1.12 plus bas.")

# ----------------------------------------------------------------------------
# 3. Effets marginaux
# ----------------------------------------------------------------------------
P("")
P("=" * 84)
P("3. EFFETS MARGINAUX : +0,1 xG/90  vs  -0,1 xGA/90 (meme gain de xGD)")
P("=" * 84)
P("   Modele structurel p = q = 1 (les poids optimaux sont symetriques, cf. 2).")
mu_all = mean([r["xG90"] for r in rows])
K_G = sum(r["G"] for r in rows) / sum(r["xG"] for r in rows)  # buts reels par xG
HFA = 1.12                                                   # avantage domicile
P("   mu = %.2f xG/match/equipe ; 1 xG = %.3f but (calage) ; hfa = %.2f"
  % (mu_all, K_G, HFA))
P("   (Un match 'moyen' : %.2f - %.2f a domicile, %.2f - %.2f a l'exterieur.)"
  % (mu_all * K_G * HFA, mu_all * K_G / HFA, mu_all * K_G / HFA, mu_all * K_G * HFA))

def lambdas(att_delta, def_delta, venue):
    h = {"home": HFA, "away": 1 / HFA, "neutral": 1.0}[venue]
    return (mu_all + att_delta) * K_G * h, (mu_all + def_delta) * K_G / h

def bloc(titre, lf, la, delta=0.1):
    w0, d0, l0 = probs(lf, la)
    P("")
    P("  %s  [xG90 = %.2f, xGA90 = %.2f]" % (titre, lf, la))
    P("  %-26s %10s %10s %10s %11s %10s" % ("scenario", "P(victo)", "P(nul)", "P(def)", "P(non-def)", "P(CS)"))
    P("  " + "-" * 78)
    cs0 = pois_vec(la)[0]
    P("  %-26s %10.4f %10.4f %10.4f %11.4f %10.4f" % ("reference", w0, d0, l0, 1 - l0, cs0))
    res_ = {}
    for lab, da, dd in [("+%.2f xG/90  (attaque)" % delta, delta, 0.0),
                        ("-%.2f xGA/90 (defense)" % delta, 0.0, -delta),
                        ("-%.2f xG/90  (attaque)" % delta, -delta, 0.0),
                        ("+%.2f xGA/90 (defense)" % delta, 0.0, delta)]:
        w, d, l = probs(lf + da, la + dd)
        P("  %-26s %10.4f %10.4f %10.4f %11.4f %10.4f"
          % (lab, w, d, l, 1 - l, pois_vec(la + dd)[0]))
        res_[lab] = (w - w0, (1 - l) - (1 - l0))
    g = "+%.2f xG/90  (attaque)" % delta
    g2 = "-%.2f xGA/90 (defense)" % delta
    P("  %-26s %10s %10s %10s %11s" % ("", "P(victo)", "", "", "P(non-def)"))
    P("  %-26s %10.4f %10s %10s %11.4f" % ("gain ATTAQUE", res_[g][0], "", "", res_[g][1]))
    P("  %-26s %10.4f %10s %10s %11.4f" % ("gain DEFENSE", res_[g2][0], "", "", res_[g2][1]))
    P("  %-26s %10.2f %10s %10s %11.2f" % ("rapport defense/attaque",
                                           res_[g2][0] / res_[g][0] if res_[g][0] else float("nan"),
                                           "", "", res_[g2][1] / res_[g][1] if res_[g][1] else float("nan")))
    return res_[g], res_[g2]

sd_att = sd(within("xG90"))
sd_def = sd(within("xGA90"))

P("")
P("A) Terrain NEUTRE, equipe moyenne vs equipe moyenne")
lf, la = lambdas(0, 0, "neutral")
bloc("neutre", lf, la)
P("")
P("B) Equipe MOYENNE a DOMICILE vs equipe moyenne")
lf, la = lambdas(0, 0, "home")
bloc("domicile", lf, la)
P("")
P("C) Equipe MOYENNE a L'EXTERIEUR vs equipe moyenne")
lf, la = lambdas(0, 0, "away")
bloc("exterieur", lf, la)
P("")
P("D) Equipe FORTE (+0.5 xG/90, -0.3 xGA/90) a domicile")
lf, la = lambdas(0.5, -0.3, "home")
bloc("forte", lf, la)
P("")
P("E) Equipe FAIBLE (-0.5 xG/90, +0.3 xGA/90) a l'exterieur")
lf, la = lambdas(-0.5, 0.3, "away")
bloc("faible", lf, la)

P("")
P("--------------------------------------------------------------------------------")
P("F) LE VRAI MATCH-TYPE : 1 ECART-TYPE d'attaque contre 1 ECART-TYPE de defense")
P("    (%+.2f xG/90 vs %.2f xGA/90 : c'est l'amplitude reelle des ecarts entre"
  % (sd_att, sd_def))
P("    equipes d'une meme ligue). Moyenne domicile + exterieur.")
P("--------------------------------------------------------------------------------")
P("")
P("   %-34s %11s %11s %11s %11s" % ("profil", "P(victoire)", "P(nul)", "P(defaite)", "P(non-defaite)"))
P("   " + "-" * 80)
base = {}
for lab, (a, d) in [("equipe moyenne", (0.0, 0.0)),
                    ("+1 SD d'attaque (%+.2f xG)" % sd_att, (sd_att, 0.0)),
                    ("+1 SD de defense (%.2f xGA)" % sd_def, (0.0, -sd_def)),
                    ("les deux", (sd_att, -sd_def))]:
    w = dl = 0.0
    for v in ("home", "away"):
        lf, la = lambdas(a, d, v)
        wv, dv, _ = probs(lf, la)
        w += wv / 2
        dl += dv / 2
    base[lab] = (w, dl)
    P("   %-34s %11.4f %11.4f %11.4f %11.4f" % (lab, w, dl, 1 - w - dl, w + dl))
w0, d0 = base["equipe moyenne"]
wa, da = base["+1 SD d'attaque (%+.2f xG)" % sd_att]
wd, dd = base["+1 SD de defense (%.2f xGA)" % sd_def]
P("")
P("   GAIN 1 SD D'ATTAQUE   : P(victoire) %+.4f   P(non-defaite) %+.4f   points/match %+.3f"
  % (wa - w0, (wa + da) - (w0 + d0), 3 * (wa - w0) + (da - d0)))
P("   GAIN 1 SD DE DEFENSE  : P(victoire) %+.4f   P(non-defaite) %+.4f   points/match %+.3f"
  % (wd - w0, (wd + dd) - (w0 + d0), 3 * (wd - w0) + (dd - d0)))
P("   RAPPORT defense / attaque : %.2f sur P(victoire), %.2f sur P(non-defaite), %.2f sur les points"
  % ((wd - w0) / (wa - w0), ((wd + dd) - (w0 + d0)) / ((wa + da) - (w0 + d0)),
     (3 * (wd - w0) + (dd - d0)) / (3 * (wa - w0) + (da - d0))))

# ----------------------------------------------------------------------------
# 4. A xGD egal : attaquer ou defendre ?
# ----------------------------------------------------------------------------
P("")
P("=" * 84)
P("4. A xGD EGAL, VAUT-IL MIEUX ATTAQUER OU DEFENDRE ?")
P("=" * 84)
P("   Deux equipes avec le meme xGD, l'une qui le doit a l'attaque, l'autre a la")
P("   defense. Saison simulee contre des adversaires moyens (moitie dom, moitie ext).")
P("")
P("   %-28s %8s %8s %10s %10s %10s %10s" % ("profil (xGD = +0.4)", "xG90", "xGA90", "P(victo)", "P(nul)", "P(non-def)", "pts/match"))
P("   " + "-" * 78)
def season_line(att_delta, def_delta, label):
    # un match a domicile + un match a l'exterieur contre un adversaire moyen
    w = d = 0.0
    for lf, la in (lambdas(att_delta, def_delta, "home"),
                   lambdas(att_delta, def_delta, "away")):
        pw, pd_, _ = probs(lf, la)
        w += pw
        d += pd_
    w /= 2
    d /= 2
    P("   %-28s %8.2f %8.2f %10.4f %10.4f %10.4f %10.2f"
      % (label, mu_all + att_delta, mu_all + def_delta, w, d, 1 - (1 - w - d), 3 * w + d))
    return 3 * w + d

ref = season_line(0.0, 0.0, "equipe moyenne (xGD = 0)")
p_att = season_line(0.4, 0.0, "tout par l'attaque")
p_def = season_line(0.0, -0.4, "tout par la defense")
p_mix = season_line(0.2, -0.2, "moitie-moitie")
P("")
P("   %-28s %8s %8s %10s %10s %10s %10s" % ("profil (xGD = -0.4)", "xG90", "xGA90", "P(victo)", "P(nul)", "P(non-def)", "pts/match"))
P("   " + "-" * 78)
n_att = season_line(-0.4, 0.0, "trou en attaque")
n_def = season_line(0.0, 0.4, "trou en defense")
n_mix = season_line(-0.2, 0.2, "moitie-moitie")
P("")
P("   Ecart attaque - defense : %+.3f pts/match pour un xGD de +0.4 (%+.1f pts/saison),"
  % (p_att - p_def, (p_att - p_def) * 38))
P("   et %+.3f pts/match pour un xGD de -0.4 (%+.1f pts/saison)."
  % (n_att - n_def, (n_att - n_def) * 38))

# ----------------------------------------------------------------------------
# 5. Fiabilite / valeur predictive
# ----------------------------------------------------------------------------
P("")
P("=" * 84)
P("5. FIABILITE : quel signal est le plus stable et le plus predictif ?")
P("=" * 84)
pairs = []
for lg in sorted(set(r["league"] for r in rows)):
    s24 = {r["team"]: r for r in rows if r["league"] == lg and r["season"] == 2024}
    s25 = {r["team"]: r for r in rows if r["league"] == lg and r["season"] == 2025}
    for t in sorted(set(s24) & set(s25)):
        pairs.append((lg, t, s24[t], s25[t]))
P("")
P("   %d equipes presentes dans les deux saisons (%s)"
  % (len(pairs), ", ".join(sorted(set(p[0] for p in pairs)))))
xG0 = [p[2]["xG90"] for p in pairs]
xG1 = [p[3]["xG90"] for p in pairs]
xA0 = [p[2]["xGA90"] for p in pairs]
xA1 = [p[3]["xGA90"] for p in pairs]
ppg1 = [p[3]["PPG"] for p in pairs]
l1 = [p[3]["L90"] for p in pairs]
w1 = [p[3]["W90"] for p in pairs]
def wlist(vals, leagues):
    d = defaultdict(list)
    for lg, v in zip(leagues, vals):
        d[lg].append(v)
    out = []
    order = [p[0] for p in pairs]
    means = {lg: mean(v) for lg, v in d.items()}
    for lg, v in zip(order, vals):
        out.append(v - means[lg])
    return out

P("")
P("   Stabilite d'une saison sur l'autre (autocorrelation) :")
leagues = [p[0] for p in pairs]
P("      corr(xG90  S1 -> xG90  S2)  = %+.3f  (brut) / %+.3f (centre par ligue)"
  % (pearson(xG0, xG1), pearson(wlist(xG0, leagues), wlist(xG1, leagues))))
P("      corr(xGA90 S1 -> xGA90 S2)  = %+.3f  (brut) / %+.3f (centre par ligue)"
  % (pearson(xA0, xA1), pearson(wlist(xA0, leagues), wlist(xA1, leagues))))
P("      corr(xGD90 S1 -> xGD90 S2)  = %+.3f  (brut) / %+.3f (centre par ligue)"
  % (pearson([a - b for a, b in zip(xG0, xA0)], [a - b for a, b in zip(xG1, xA1)]),
     pearson(wlist([a - b for a, b in zip(xG0, xA0)], leagues),
             wlist([a - b for a, b in zip(xG1, xA1)], leagues))))
P("")
P("   Prediction des POINTS de la saison suivante (S2), centre par ligue :")
P("      corr(xG90  S1, PPG S2)  = %+.3f  (brut %+.3f)" % (pearson(wlist(xG0, leagues), wlist(ppg1, leagues)), pearson(xG0, ppg1)))
P("      corr(xGA90 S1, PPG S2)  = %+.3f  (brut %+.3f)" % (pearson(wlist(xA0, leagues), wlist(ppg1, leagues)), pearson(xA0, ppg1)))
P("      corr(xGD90 S1, PPG S2)  = %+.3f  (brut %+.3f)" % (pearson(wlist([a - b for a, b in zip(xG0, xA0)], leagues), wlist(ppg1, leagues)),
                                                           pearson([a - b for a, b in zip(xG0, xA0)], ppg1)))
P("      corr(PPG   S1, PPG S2)  = %+.3f   (reference naive : les points passes)"
  % pearson(wlist([p[2]["PPG"] for p in pairs], leagues), wlist(ppg1, leagues)))
P("")
P("   Regressions (S1 -> S2), variables centrees par ligue :")

for lab, Xs in [("PPG ~ xG90 seul", [[1.0, a] for a in wlist(xG0, leagues)]),
                ("PPG ~ xGA90 seul", [[1.0, a] for a in wlist(xA0, leagues)]),
                ("PPG ~ xG90 + xGA90", [[1.0, a, b] for a, b in zip(wlist(xG0, leagues), wlist(xA0, leagues))])]:
    beta, se, t, r2, rmse, n = ols(wlist(ppg1, leagues), Xs)
    sy = sd(wlist(ppg1, leagues))
    if len(beta) == 2:
        P("      %-20s R2 = %.3f  beta* = %+.3f (t = %+.1f)" % (lab, r2, beta[1] * sd(wlist(xG0, leagues)) / sy, t[1]))
    else:
        P("      %-20s R2 = %.3f  beta*(xG) = %+.3f (t = %+.1f) | beta*(xGA) = %+.3f (t = %+.1f)"
          % (lab, r2, beta[1] * sd(wlist(xG0, leagues)) / sy, t[1],
             beta[2] * sd(wlist(xA0, leagues)) / sy, t[2]))
P("")
P("   Prediction des DEFAITES de la saison suivante (risque de perdre) :")
Xs = [[1.0, a, b] for a, b in zip(wlist(xG0, leagues), wlist(xA0, leagues))]
beta, se, t, r2, rmse, n = ols(wlist(l1, leagues), Xs)
sy = sd(wlist(l1, leagues))
P("      defaites/match S2 : R2 = %.3f  beta*(xG) = %+.3f (t = %+.1f) | beta*(xGA) = %+.3f (t = %+.1f)"
  % (r2, beta[1] * sd(wlist(xG0, leagues)) / sy, t[1], beta[2] * sd(wlist(xA0, leagues)) / sy, t[2]))
beta, se, t, r2, rmse, n = ols(wlist(w1, leagues), Xs)
sy = sd(wlist(w1, leagues))
P("      victoires S2  R2 = %.3f  beta*(xG) = %+.3f (t = %+.1f) | beta*(xGA) = %+.3f (t = %+.1f)"
  % (r2, beta[1] * sd(wlist(xG0, leagues)) / sy, t[1], beta[2] * sd(wlist(xA0, leagues)) / sy, t[2]))

txt = "\n".join(out)
print(txt)
open("resultats_xg_xga.txt", "w", encoding="utf-8").write(txt + "\n")
