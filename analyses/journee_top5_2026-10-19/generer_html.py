# -*- coding: utf-8 -*-
"""Version HTML autonome du bilan (aucune dépendance externe)."""
import os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from donnees_h2h import MATCHES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bilan.html")

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
        m["verdict"] = None
        if m["fav"] == "home":
            m["verdict"] = "ok" if m["res"] in ("H", "D") else "ko"
        elif m["fav"] == "away":
            m["verdict"] = "ok" if m["res"] in ("A", "D") else "ko"
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
by_league = defaultdict(list)
for m in MATCHES:
    by_league[m["league"]].append(m)


def nom_fav(m):
    return m["home"] if m["fav"] == "home" else m["away"]


def fr(x, dec=0):
    return f"{x:.{dec}f}".replace(".", ",")


def badge(m):
    if not m["score"]:
        return '<span class="b wait">à jouer</span>'
    if m["n"] == 0 or not m["fav"]:
        return '<span class="b na">non applicable</span>'
    return '<span class="b ok">validé</span>' if m["verdict"] == "ok" else '<span class="b ko">contredit</span>'


stats = {}
for lg in LEAGUES:
    sub = [m for m in by_league[lg] if m["score"]]
    app = [m for m in sub if m["fav"]]
    o = [m for m in app if m["verdict"] == "ok"]
    stats[lg] = (len(app), len(o), 100 * len(o) / len(app) if app else 0)

cards = [
    ("48", "matchs au programme", "10 + 10 + 10 + 9 + 9"),
    (f"{len(applicable)}", "matchs arbitrés par la règle", f"{len(equal)} à égalité · {len(zero)} sans historique"),
    (f"{fr(rate,1)} %", "de réussite", f"{len(ok)} validés · {len(ko)} contredits"),
    ("1 / 5", "de réussite en Serie A", "le championnat qui la contredit le plus"),
]

rows = []
for m in MATCHES:
    h2h = ""
    if m["n"] == 0:
        h2h = ("<p class='note'>" + RAISONS_ZERO.get((m["home"], m["away"]),
               "Aucune confrontation en championnat sur les deux dernières saisons.") + "</p>")
    else:
        lines = []
        for season in ("2025-26", "2024-25"):
            parts = [f"{h} <b>{hs}-{as_}</b> {a}" for s, h, a, hs, as_ in m["h2h"] if s == season]
            if parts:
                lines.append(f"<li><span class='season'>{season}</span> " + " &nbsp;·&nbsp; ".join(parts) + "</li>")
        h2h = "<ul class='h2h'>" + "".join(lines) + "</ul>"
        if m["fav"]:
            h2h += (f"<p class='fav'>Favori : <b>{nom_fav(m)}</b> — {m['hw']} v. / {m['dr']} n. / {m['aw']} d. "
                    f"sur {m['n']} confrontation{'s' if m['n'] > 1 else ''}</p>")
        else:
            h2h += ("<p class='fav'>Aucun favori : égalité parfaite du nombre de victoires "
                    f"({m['hw']} – {m['dr']} – {m['aw']}).</p>")
    rows.append(f"""
    <details class="match">
      <summary>
        <span class="score">{m['score'] or '–'}</span>
        <span class="teams">{m['home']} <span class="vs">/</span> {m['away']}</span>
        {badge(m)}
      </summary>
      <div class="body">{h2h}</div>
    </details>""")

sections = []
for lg in LEAGUES:
    app, o, r = stats[lg]
    sections.append(f"""
    <section>
      <div class="lghead"><h2>{lg}</h2><div class="lgrate">{fr(r)} %<small>{o}/{app} arbitrés</small></div></div>
      {''.join(x for x, mm in zip(rows, MATCHES) if mm['league'] == lg)}
    </section>""")

HTML = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bilan H2H — dernière journée du top 5 européen</title>
<style>
  :root {{ --ink:#101820; --muted:#64748b; --line:#e2e8f0; --bg:#f6f7f9; --ok:#0f766e; --ko:#b91c1c; --na:#94a3b8; --wait:#b45309; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI",system-ui,-apple-system,sans-serif; line-height:1.5; }}
  .wrap {{ max-width:1000px; margin:0 auto; padding:36px 20px 60px; }}
  header {{ border-bottom:3px solid var(--ink); padding-bottom:20px; margin-bottom:26px; }}
  .kicker {{ text-transform:uppercase; letter-spacing:.14em; font-size:12px; color:var(--muted); font-weight:700; }}
  h1 {{ font-size:34px; line-height:1.15; margin:8px 0 10px; }}
  .lead {{ color:#334155; max-width:70ch; }}
  .quote {{ border-left:4px solid var(--ink); padding:8px 16px; color:#334155; font-style:italic; margin:18px 0 0; }}
  .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:26px 0; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px 16px; }}
  .card b {{ display:block; font-size:28px; line-height:1; margin-bottom:6px; }}
  .card span {{ font-size:13px; color:#334155; display:block; }}
  .card small {{ color:var(--muted); font-size:11.5px; }}
  .panel {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:18px 20px; margin:22px 0; }}
  h2 {{ font-size:19px; margin:0; }}
  .lghead {{ display:flex; align-items:baseline; justify-content:space-between; margin:30px 0 10px; border-bottom:1px solid var(--line); padding-bottom:8px; }}
  .lgrate {{ font-weight:700; font-size:15px; }}
  .lgrate small {{ display:block; font-weight:400; color:var(--muted); font-size:11.5px; text-align:right; }}
  details.match {{ background:#fff; border:1px solid var(--line); border-radius:10px; margin-bottom:8px; }}
  details.match summary {{ list-style:none; cursor:pointer; display:flex; align-items:center; gap:12px; padding:11px 14px; }}
  details.match summary::-webkit-details-marker {{ display:none; }}
  .score {{ min-width:52px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .teams {{ flex:1; }}
  .vs {{ color:#cbd5e1; }}
  .b {{ font-size:11.5px; font-weight:700; padding:4px 9px; border-radius:999px; white-space:nowrap; }}
  .b.ok {{ background:#ccfbf1; color:var(--ok); }}
  .b.ko {{ background:#fee2e2; color:var(--ko); }}
  .b.na {{ background:#f1f5f9; color:var(--na); }}
  .b.wait {{ background:#fef3c7; color:var(--wait); }}
  .body {{ border-top:1px dashed var(--line); padding:10px 14px 6px; }}
  ul.h2h {{ margin:4px 0 8px; padding-left:18px; }}
  ul.h2h li {{ margin:3px 0; font-size:14px; }}
  .season {{ display:inline-block; min-width:58px; color:var(--muted); font-weight:600; font-size:12px; }}
  .fav {{ margin:6px 0 8px; font-size:13.5px; color:#334155; }}
  .note {{ font-size:13.5px; color:#475569; margin:4px 0 8px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th, td {{ text-align:left; padding:8px 6px; border-bottom:1px solid var(--line); }}
  th {{ font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
  td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .bar {{ height:6px; background:#e2e8f0; border-radius:99px; overflow:hidden; }}
  .bar i {{ display:block; height:100%; background:var(--ok); }}
  .split {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  ul.clean {{ padding-left:18px; margin:8px 0 0; }}
  ul.clean li {{ margin:6px 0; font-size:14.5px; }}
  .foot {{ margin-top:34px; color:var(--muted); font-size:12.5px; border-top:1px solid var(--line); padding-top:14px; }}
  @media (max-width:760px) {{ .cards {{ grid-template-columns:repeat(2,1fr); }} .split {{ grid-template-columns:1fr; }} h1 {{ font-size:26px; }} }}
  @media print {{ details.match {{ break-inside:avoid; }} details.match .body {{ display:block; }} }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">Bilan à la loupe · 16-19 octobre 2026</div>
  <h1>La règle des confrontations directes<br>sur la dernière journée du top 5 européen</h1>
  <p class="lead">Premier League (J7), Liga (J9), Serie A (J7), Bundesliga (J6), Ligue 1 (J7) : 48 matchs passés au crible,
  confrontation par confrontation, sur les deux dernières saisons de championnat.</p>
  <p class="quote">« Les équipes ayant remporté le plus de matchs dans les confrontations directes des 2 dernières années
  font victoire ou match nul dans le match du jour. »</p>
</header>

<div class="cards">
  {''.join(f'<div class="card"><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in cards)}
</div>

<div class="panel">
  <h2>Le bilan par championnat</h2>
  <table>
    <thead><tr><th>Championnat</th><th class="num">Arbitrés</th><th class="num">Validés</th><th class="num">Contredits</th><th>Taux</th></tr></thead>
    <tbody>
    {''.join(f'''<tr><td>{lg}</td><td class="num">{stats[lg][0]}</td><td class="num">{stats[lg][1]}</td>
      <td class="num">{stats[lg][0]-stats[lg][1]}</td>
      <td><div style="display:flex;align-items:center;gap:8px"><div class="bar" style="flex:1"><i style="width:{stats[lg][2] if stats[lg][0] else 0}%"></i></div>
      <span style="font-size:12.5px;font-weight:700;min-width:42px">{fr(stats[lg][2]) if stats[lg][0] else '—'} %</span></div></td></tr>''' for lg in LEAGUES)}
    </tbody>
  </table>
  <p class="note">La règle a fonctionné deux fois sur trois. Mais elle a été parfaite en Liga (4/4) et calamiteuse en Serie A (1/5) :
  sa valeur dépend fortement du championnat et du contexte des clubs.</p>
</div>

<div class="split">
  <div class="panel">
    <h2>Ce qui a marché</h2>
    <ul class="clean">
      <li><b>Real Madrid 4-1 Séville</b> — 4 victoires en 4 confrontations, le signal le plus net du week-end.</li>
      <li><b>Bayern 6-1 Leipzig</b> — 3 victoires et 1 nul dans l'historique.</li>
      <li><b>Trois nuls</b> ont sauvé la double chance : Leeds, Villarreal et Union Berlin.</li>
      <li><b>11 favoris à domicile sur 14</b> ont tenu (79 %), contre 8 sur 14 à l'extérieur (57 %).</li>
    </ul>
  </div>
  <div class="panel">
    <h2>Ce qui a raté</h2>
    <ul class="clean">
      <li><b>Brighton 5-0 Crystal Palace</b> — Palace avait 3 victoires et 1 nul sur 4.</li>
      <li><b>Monza 4-0 Cagliari</b> — Cagliari avait gagné les deux confrontations.</li>
      <li><b>Le Havre 1-3 Auxerre</b> et <b>Udinese 0-3 Lecce</b> — 3 victoires sur 4, et deux défaites à domicile.</li>
      <li><b>Milan 3-2 Atalanta</b> — l'Atalanta avait 3 victoires et 1 nul.</li>
    </ul>
  </div>
</div>

<div class="panel">
  <h2>Le détail, match par match</h2>
  <p class="note">Cliquez sur une ligne pour dérouler l'historique des confrontations.</p>
</div>

{''.join(sections)}

<div class="panel">
  <h2>Mode d'emploi et limites</h2>
  <ul class="clean">
    <li><b>Fenêtre :</b> saisons 2024-25 et 2025-26, championnat uniquement (coupes exclues).</li>
    <li><b>Favori :</b> le club avec strictement plus de victoires. Validé s'il gagne ou fait match nul.</li>
    <li><b>Couverture :</b> {len(equal)+len(zero)} matchs sur {len(played)} échappent au critère (égalité parfaite ou aucun historique), soit
      {fr(100*(len(equal)+len(zero))/len(played))} % de la journée.</li>
    <li><b>Prudence :</b> {len(applicable)} observations sur un seul week-end ne suffisent pas à conclure statistiquement.</li>
  </ul>
</div>

<div class="foot">
  Sources : matrices de résultats des saisons 2024-25 et 2025-26 (championnat) et résultats de la journée recoupés
  sur les sources de référence de chaque championnat. Données détaillées : <code>bilan_h2h.csv</code>.
</div>
</div>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("HTML écrit :", OUT, len(HTML), "caractères")
