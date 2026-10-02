#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCULATEUR DE MATCH - interface simple (page web) autour de modele_xg.py

    python3 calculateur.py            # ouvre http://0.0.0.0:8000

Aucune dependance : bibliotheque standard uniquement.
Tout le calcul est fait par modele_xg.py (meme code que le backtest).
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import modele_xg as mx  # noqa: E402

PORT = int(os.environ.get("PORT", "8000"))
SAISON = 2025            # derniere saison complete disponible dans data/
LIGUES = {"EPL": "Angleterre", "La_Liga": "Espagne", "Bundesliga": "Allemagne",
          "Ligue_1": "France", "Serie_A": "Italie"}
NOMS_FR = {"Bundesliga": "Bundesliga", "La_Liga": "Liga", "EPL": "Premier League",
           "Ligue_1": "Ligue 1", "Serie_A": "Serie A"}

# noms tels qu'ils apparaissent dans les menus (les cles restent celles du fichier de donnees)
AFFICHAGE = {
    "Paris Saint Germain": "Paris SG", "RasenBallsport Leipzig": "RB Leipzig",
    "Wolverhampton Wanderers": "Wolves", "Parma Calcio 1913": "Parme",
    "AC Milan": "Milan AC", "VfB Stuttgart": "Stuttgart", "FC Cologne": "Cologne",
    "Atletico Madrid": "Atlético Madrid", "Bayer Leverkusen": "Leverkusen",
    "Borussia M.Gladbach": "Mönchengladbach", "Eintracht Frankfurt": "Francfort",
    "Nottingham Forest": "Nott. Forest", "Manchester United": "Manchester Utd",
    "Manchester City": "Manchester City", "Crystal Palace": "Crystal Palace",
    "Real Sociedad": "Real Sociedad", "Rayo Vallecano": "Rayo Vallecano",
    "Athletic Club": "Athletic Bilbao", "Real Betis": "Betis Séville",
    "Brighton": "Brighton", "Tottenham": "Tottenham", "Newcastle United": "Newcastle",
}


def nom(t):
    return AFFICHAGE.get(t, t)

# ---------------------------------------------------------------------------
# Preparation des donnees : une table par ligue, saison 2025/26
# ---------------------------------------------------------------------------
PAR_LIGUE = {}
for lg in LIGUES:
    grp = [r for r in mx.rows if r["league"] == lg and r["season"] == SAISON]
    if not grp:
        continue
    mu, A, D, wa, wd = mx.ratings(grp)
    PAR_LIGUE[lg] = {"mu": mu, "A": A, "D": D, "w_att": wa, "w_def": wd,
                     "equipes": sorted(A)}


def pct(x):
    return round(100 * x, 1)


def force_en_mots(v, sens="att"):
    """Traduit un rating (1,00 = moyenne de la ligue) en langage courant.
    sens='att' : plus c'est haut, mieux c'est.
    sens='def' : D mesure les xG concédés, donc plus c'est BAS, mieux c'est."""
    e = 100 * (v - 1)
    if abs(e) < 4:
        return "dans la moyenne"
    if sens == "att":
        mot = ("excellente" if e >= 25 else "très bonne" if e >= 12 else "correcte"
               if e > 0 else "faible" if e > -12 else "très faible" if e > -25
               else "catastrophique")
    else:
        mot = ("catastrophique" if e >= 25 else "très fragile" if e >= 12 else "fragile"
               if e > 0 else "solide" if e > -12 else "très solide" if e > -25
               else "excellente")
    return f"{mot} ({'+' if e > 0 else ''}{e:.0f} % de xG concédés)" if sens == "def" \
        else f"{mot} ({'+' if e > 0 else ''}{e:.0f} % de xG créés)"


def analyse(home, away, cotes, lg, manuel=None):
    """cotes = dict marche -> cote bookmaker (ou None). Retourne le JSON.
    Les pourcentages affiches sont les ecarts BRUTS (verifiables sur Understat) ;
    la reduction vers la moyenne n'agit que sur le calcul des buts attendus."""
    if manuel:
        mu = PAR_LIGUE[lg]["mu"] if lg in PAR_LIGUE else 1.55
        n = manuel["n"]
        wa = mx.fiabilite(n, mx.RHO_ATT)
        wd = mx.fiabilite(n, mx.RHO_DEF)
        A = {home: (manuel["xg_h"] / mu) ** wa, away: (manuel["xg_a"] / mu) ** wa}
        D = {home: (manuel["xga_h"] / mu) ** wd, away: (manuel["xga_a"] / mu) ** wd}
        brut = {(home, "a"): manuel["xg_h"] / mu, (away, "a"): manuel["xg_a"] / mu,
                (home, "d"): manuel["xga_h"] / mu, (away, "d"): manuel["xga_a"] / mu}
        source = f"saisie manuelle sur {int(n)} derniers matchs"
        poids = f"crédit accordé à l'attaque : {wa:.0%} · à la défense : {wd:.0%} (échantillon de {int(n)} matchs)"
    else:
        info = PAR_LIGUE[lg]
        mu, A, D = info["mu"], info["A"], info["D"]
        source = f"saison {SAISON}/{SAISON + 1} complete ({NOMS_FR.get(lg, lg)})"
        grp = [r for r in mx.rows if r["league"] == lg and r["season"] == SAISON]
        brut = {(r["team"], "a"): r["xG90"] / mu for r in grp}
        brut.update({(r["team"], "d"): r["xGA90"] / mu for r in grp})
        poids = f"crédit accordé à l'attaque : {info['w_att']:.0%} · à la défense : {info['w_def']:.0%} (saison complète)"

    hn, an = nom(home), nom(away)
    lh, la = mx.lambdas(home, away, mu, A, D)
    p1, px, p2 = mx.probas(lh, la)
    tot, btts, cs_h, cs_a = mx.buts(lh, la)

    marches = [
        ("1", f"Victoire {hn}", p1),
        ("X", "Match nul", px),
        ("2", f"Victoire {an}", p2),
        ("1X", f"{hn} ne perd pas", p1 + px),
        ("X2", f"{an} ne perd pas", px + p2),
        ("O25", "Plus de 2,5 buts", tot[2.5]),
        ("U25", "Moins de 2,5 buts", 1 - tot[2.5]),
        ("BTTS", "Les deux équipes marquent", btts),
    ]
    out_m = []
    verdicts = []
    for code, libelle, p in marches:
        cote = cotes.get(code)
        ligne = {"code": code, "libelle": libelle, "p": pct(p), "cote_juste": round(1 / p, 2)}
        if cote and cote > 1:
            edge = mx.value(p, cote)
            mise = mx.kelly(p, cote)
            ligne.update({"cote": cote, "edge": round(100 * edge, 1) or 0.0,
                          "mise": round(100 * mise, 2)})
            if edge > 0:
                verdicts.append((edge, libelle, p, cote, mise))
        out_m.append(ligne)

    saisies = [l for l in out_m if "cote" in l]
    verdicts.sort(reverse=True)
    if not saisies:
        niveau, couleur = "INFO", "gris"
        phrase = ("Voici les probabilités. Entrez les cotes de votre bookmaker "
                  "pour savoir s'il y a de la valeur.")
        conseil = ""
    elif verdicts and verdicts[0][0] > 0:
        edge, libelle, p, cote, mise = verdicts[0]
        if edge >= 0.15:
            niveau, couleur = "AVANTAGE SUSPECT", "orange"
            phrase = (f"Cote {cote:g} sur \"{libelle}\" (juste : {1 / p:.2f}), avantage "
                      f"{edge * 100:.0f} %. Un avantage aussi gros n'existe presque jamais : "
                      f"vérifiez d'abord vos chiffres (blessés, compos, xG récents).")
        elif edge >= 0.05:
            niveau, couleur = "BONNE COTE", "vert"
            phrase = (f"Le bookmaker offre {cote:g} sur \"{libelle}\" alors que la cote "
                      f"juste est {1 / p:.2f}. Avantage de {edge * 100:.1f} %.")
        elif edge >= 0.02:
            niveau, couleur = "LEGER AVANTAGE", "orange"
            phrase = (f"Cote {cote:g} sur \"{libelle}\" (juste : {1 / p:.2f}). "
                      f"Avantage faible : {edge * 100:.1f} %. Dans le bruit.")
        else:
            niveau, couleur = "PAS DE VALEUR", "rouge"
            phrase = (f"La meilleure de vos cotes est {cote:g} sur \"{libelle}\" "
                      f"(juste : {1 / p:.2f}) : avantage {edge * 100:.1f} %, "
                      f"trop faible pour jouer.")
        conseil = (f"Mise conseillée : {mise * 100:.1f} EUR pour 100 EUR de bankroll "
                   f"(soit 1/4 de Kelly)." if mise > 0 else
                   "Pas de mise : l'avantage est nul ou négatif.")
    else:
        meilleure = max(saisies, key=lambda l: l["edge"])
        niveau, couleur = "PAS DE VALEUR", "rouge"
        phrase = (f"Aucune de vos cotes ne bat la cote juste. La moins mauvaise : "
                  f"{meilleure['cote']:g} sur \"{meilleure['libelle']}\" "
                  f"(juste : {meilleure['cote_juste']:g}, soit "
                  f"{meilleure['edge']:+.1f} %). Ne jouez pas ce match.")
        conseil = "Pas de mise."

    return {
        "home": hn, "away": an, "ligue": NOMS_FR.get(lg, lg), "source": source,
        "poids": poids,
        "buts_home": round(lh, 2), "buts_away": round(la, 2),
        "buts_total": round(lh + la, 2),
        "att_home": force_en_mots(brut[(home, "a")], "att"),
        "def_home": force_en_mots(brut[(home, "d")], "def"),
        "att_away": force_en_mots(brut[(away, "a")], "att"),
        "def_away": force_en_mots(brut[(away, "d")], "def"),
        "p1": pct(p1), "px": pct(px), "p2": pct(p2),
        "cote1": round(1 / p1, 2), "cotex": round(1 / px, 2), "cote2": round(1 / p2, 2),
        "marches": out_m,
        "niveau": niveau, "couleur": couleur, "phrase": phrase, "conseil": conseil,
        "faveur": (hn if p1 > p2 else an) if max(p1, p2) > 0.40 else None,
        "p_faveur": pct(max(p1, p2)),
    }


# ---------------------------------------------------------------------------
# Serveur HTTP
# ---------------------------------------------------------------------------
PAGE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analyseur de match - xG / xGA</title>
<style>
:root{--vert:#15803d;--rouge:#b91c1c;--orange:#b45309;--fond:#f6f7f9;--carte:#fff;--bord:#e3e6ea}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
background:var(--fond);color:#16181d;line-height:1.5}
.wrap{max-width:760px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:8px 0 4px}
.sous{color:#5b6472;font-size:14px;margin:0 0 18px}
.carte{background:var(--carte);border:1px solid var(--bord);border-radius:12px;padding:16px;margin-bottom:14px}
label{display:block;font-weight:600;font-size:14px;margin:12px 0 4px}
select,input{width:100%;padding:12px;font-size:16px;border:1px solid #c9ced6;border-radius:8px;background:#fff}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
button{width:100%;padding:16px;font-size:18px;font-weight:700;color:#fff;background:#0f766e;
border:0;border-radius:10px;margin-top:16px;cursor:pointer}
button:active{transform:scale(.99)}
.verdict{border-radius:12px;padding:16px;color:#fff;font-size:17px;margin-bottom:14px}
.verdict b{display:block;font-size:24px;margin-bottom:4px}
.vert{background:var(--vert)}.rouge{background:var(--rouge)}.orange{background:var(--orange)}
.gris{background:#4b5563}
.chances{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center}
.chance{background:#f1f3f6;border-radius:10px;padding:12px 6px}
.chance .v{font-size:26px;font-weight:800}
.chance .l{font-size:12px;color:#5b6472}
.chance .c{font-size:12px;color:#0f766e;font-weight:600;margin-top:2px}
.buts{display:flex;justify-content:space-around;text-align:center;margin-bottom:12px}
.buts .v{font-size:30px;font-weight:800}
.buts .l{font-size:13px;color:#5b6472}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:9px 6px;text-align:left;border-bottom:1px solid var(--bord)}
th{font-size:12px;color:#5b6472;text-transform:uppercase;letter-spacing:.03em}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.ok{color:var(--vert);font-weight:700}.ko{color:#9aa2ad}
.puce{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:600}
.puce.o{background:#dcfce7;color:var(--vert)}
.regle{font-size:14px;color:#3b424d}
.regle li{margin-bottom:6px}
details{margin-top:8px}
summary{cursor:pointer;font-weight:600;font-size:14px;color:#0f766e}
.note{font-size:12px;color:#7b8492;margin-top:6px}
.err{color:var(--rouge);font-weight:600;margin-top:10px}
</style></head><body><div class="wrap">
<h1>Analyseur de match</h1>
<p class="sous">Vous choisissez deux equipes, l'outil dit qui gagne le plus souvent
et si la cote de votre bookmaker vaut le coup.</p>

<div class="carte">
  <label>1. Les deux equipes</label>
  <div class="grid2">
    <select id="home"><option value="">Equipe a domicile</option></select>
    <select id="away"><option value="">Equipe a l'exterieur</option></select>
  </div>
  <label>2. Les cotes de votre bookmaker (laissez vide si vous ne les avez pas)</label>
  <div class="grid3">
    <input id="c1" type="number" step="0.01" placeholder="Cote 1">
    <input id="cx" type="number" step="0.01" placeholder="Cote X">
    <input id="c2" type="number" step="0.01" placeholder="Cote 2">
  </div>
  <div class="grid3" style="margin-top:8px">
    <input id="c1X" type="number" step="0.01" placeholder="1X (ne perd pas)">
    <input id="cO" type="number" step="0.01" placeholder="Plus de 2,5 buts">
    <input id="cB" type="number" step="0.01" placeholder="Les deux marquent">
  </div>
  <button onclick="go()">Analyser le match</button>
  <details><summary>J'ai des chiffres plus recents (mode manuel)</summary>
    <p class="note">Si vous avez les xG des 5-10 derniers matchs (Understat, FBref),
    entrez-les ici en buts par match. L'outil tient compte de la taille de l'echantillon.</p>
    <label>Nombre de matchs pris en compte</label>
    <input id="mn" type="number" value="10" min="3" max="38">
    <div class="grid2">
      <div><label class="note">xG/match - domicile</label><input id="mxg_h" type="number" step="0.01" placeholder="1,80"></div>
      <div><label class="note">xG/match - exterieur</label><input id="mxg_a" type="number" step="0.01" placeholder="1,40"></div>
      <div><label class="note">xG concédés/match - domicile</label><input id="mxga_h" type="number" step="0.01" placeholder="1,10"></div>
      <div><label class="note">xG concédés/match - exterieur</label><input id="mxga_a" type="number" step="0.01" placeholder="1,30"></div>
    </div>
  </details>
</div>

<div id="out"></div>

<div class="carte">
  <b>Les 4 regles a retenir</b>
  <ul class="regle">
    <li><b>Jouez seulement si la cote proposee depasse la cote juste de 5 %.</b> En dessous, c'est du bruit.</li>
    <li><b>Mise : 1 a 2 % de votre bankroll</b> (l'outil donne le chiffre exact, base 1/4 de Kelly).</li>
    <li><b>Ne jugez jamais une defense sur 5 matchs.</b> C'est le signal le plus trompeur :
    sur 5 matchs il ne compte que pour 13 %.</li>
    <li><b>Sur « ne pas perdre » (1X, X2), la defense compte autant que l'attaque.</b>
    Sur « qui gagne », c'est l'attaque qui decide.</li>
  </ul>
</div>
</div>
<script>
const LIGUES=__LIGUES__;
const HOME=document.getElementById('home'), AWAY=document.getElementById('away');
for(const lg in LIGUES){
  for(const sel of [HOME,AWAY]){
    const og=document.createElement('optgroup'); og.label=LIGUES[lg];
    for(const t in LIGUES[lg]){const o=document.createElement('option');o.value=lg+'|'+t;o.textContent=LIGUES[lg][t];og.appendChild(o);}
    sel.appendChild(og);
  }
}
HOME.value='EPL|Arsenal'; AWAY.value='EPL|Manchester City';
function num(id){const v=parseFloat(document.getElementById(id).value.replace(',','.'));return isFinite(v)&&v>1?v:null;}
async function go(){
  const out=document.getElementById('out'); out.innerHTML='<p class="note">Calcul...</p>';
  const h=HOME.value.split('|'), a=AWAY.value.split('|');
  if(!h[1]||!a[1]){out.innerHTML='<p class="err">Choisissez les deux equipes.</p>';return;}
  const cotes={};
  const map={c1:'1',cx:'X',c2:'2',c1X:'1X',cO:'O25',cB:'BTTS'};
  for(const k in map){const v=num(k); if(v)cotes[map[k]]=v;}
  let manuel=null;
  const n=parseFloat(document.getElementById('mn').value);
  const q=['mxg_h','mxg_a','mxga_h','mxga_a'].map(num);
  if(q.every(x=>x)) manuel={n:n||10,xg_h:q[0],xg_a:q[1],xga_h:q[2],xga_a:q[3]};
  const u='/api/match?home='+encodeURIComponent(h[1])+'&away='+encodeURIComponent(a[1])
      +'&lg='+h[0]+'&cotes='+encodeURIComponent(JSON.stringify(cotes))
      +(manuel?'&manuel='+encodeURIComponent(JSON.stringify(manuel)):'');
  const r=await fetch(u);
  if(!r.ok){out.innerHTML='<p class="err">'+(await r.text())+'</p>';return;}
  const d=await r.json();
  let html='<div class="verdict '+d.couleur+'"><b>'+d.niveau+'</b>'+d.phrase
    +(d.conseil?'<br><b style="font-size:17px;margin-top:8px">'+d.conseil+'</b>':'')+'</div>';
  html+='<div class="carte"><b>'+d.home+' &nbsp;-&nbsp; '+d.away+'</b>'
    +'<div class="note">'+d.source+' &middot; '+d.poids+'</div>'
    +'<div class="buts" style="margin-top:12px">'
    +'<div><div class="v">'+d.buts_home.toFixed(2).replace('.',',')+'</div><div class="l">buts attendus<br>'+d.home+'</div></div>'
    +'<div><div class="v">'+d.buts_total.toFixed(2).replace('.',',')+'</div><div class="l">buts attendus<br>au total</div></div>'
    +'<div><div class="v">'+d.buts_away.toFixed(2).replace('.',',')+'</div><div class="l">buts attendus<br>'+d.away+'</div></div>'
    +'</div>'
    +'<div class="chances">'
    +'<div class="chance"><div class="v">'+d.p1+'%</div><div class="l">victoire '+d.home+'</div><div class="c">cote juste '+d.cote1.toString().replace('.',',')+'</div></div>'
    +'<div class="chance"><div class="v">'+d.px+'%</div><div class="l">match nul</div><div class="c">cote juste '+d.cotex.toString().replace('.',',')+'</div></div>'
    +'<div class="chance"><div class="v">'+d.p2+'%</div><div class="l">victoire '+d.away+'</div><div class="c">cote juste '+d.cote2.toString().replace('.',',')+'</div></div>'
    +'</div></div>';
  html+='<div class="carte"><b>Lecture des deux equipes</b><table>'
    +'<tr><th></th><th>Attaque</th><th>Defense</th></tr>'
    +'<tr><td>'+d.home+'</td><td>'+d.att_home+'</td><td>'+d.def_home+'</td></tr>'
    +'<tr><td>'+d.away+'</td><td>'+d.att_away+'</td><td>'+d.def_away+'</td></tr></table></div>';
  html+='<div class="carte"><b>Tous les marches</b><table>'
    +'<tr><th>Marche</th><th class="n">Prob.</th><th class="n">Cote juste</th><th class="n">Cote</th><th class="n">Avantage</th><th class="n">Mise</th></tr>';
  for(const m of d.marches){
    const e=(m.edge!==undefined)?'<span class="'+(m.edge>=5?'ok':(m.edge>=2?'':'ko'))+'">'
      +(m.edge>0?'+':'')+m.edge.toString().replace('.',',')+'%</span>':'<span class="ko">-</span>';
    html+='<tr><td>'+m.libelle+'</td><td class="n">'+m.p+'%</td><td class="n">'
      +m.cote_juste.toString().replace('.',',')+'</td><td class="n">'
      +(m.cote?m.cote.toString().replace('.',','):'-')+'</td><td class="n">'+e+'</td><td class="n">'
      +(m.mise?m.mise.toString().replace('.',',')+'%':'-')+'</td></tr>';
  }
  html+='</table><div class="note">« Avantage » = ce que la cote proposee rapporte de plus que la cote juste. '
    +'Mise = part de votre bankroll (1/4 de Kelly).</div></div>';
  out.innerHTML=html;
}
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            self._send(200, PAGE.replace("__LIGUES__", json.dumps(
                {k: {t: nom(t) for t in v["equipes"]} for k, v in PAR_LIGUE.items()},
                ensure_ascii=False)),
                "text/html; charset=utf-8")
            return
        if u.path == "/api/ligues":
            self._send(200, json.dumps(PAR_LIGUE.keys(), ensure_ascii=False))
            return
        if u.path == "/api/match":
            q = parse_qs(u.query)
            try:
                home = q["home"][0]
                away = q["away"][0]
                lg = q.get("lg", ["EPL"])[0]
                cotes = json.loads(q.get("cotes", ["{}"])[0])
                manuel = json.loads(q["manuel"][0]) if "manuel" in q else None
                if home == away:
                    raise ValueError("Les deux équipes doivent être différentes.")
                if lg not in PAR_LIGUE:
                    raise ValueError("Ligue inconnue : " + lg)
                if not manuel:
                    for t in (home, away):
                        if t not in PAR_LIGUE[lg]["A"]:
                            raise ValueError(
                                f"{t} n'est pas dans {NOMS_FR.get(lg, lg)}. "
                                f"Equipes disponibles : {', '.join(nom(x) for x in PAR_LIGUE[lg]['equipes'])}.")
                self._send(200, json.dumps(
                    analyse(home, away, cotes, lg, manuel), ensure_ascii=False))
            except Exception as e:  # noqa: BLE001
                self._send(400, str(e), "text/plain; charset=utf-8")
            return
        self._send(404, "introuvable", "text/plain; charset=utf-8")


if __name__ == "__main__":
    print(f"Calculateur de match sur http://0.0.0.0:{PORT}")
    print(f"   ligues chargees : {', '.join(PAR_LIGUE)}")
    sys.stdout.flush()
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
