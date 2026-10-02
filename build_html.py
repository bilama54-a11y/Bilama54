#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere analyseur.html : version HORS-LIGNE, un seul fichier, aucun serveur.

Le modele est un portage fidele de modele_xg.py (meme code, meme constantes),
les donnees de la saison 2025/26 sont embarquees dans la page.
Ouvrez simplement le fichier dans n'importe quel navigateur.
"""
import csv
import json

rows = list(csv.DictReader(open("data/understat_team_seasons.csv", encoding="utf-8")))
for r in rows:
    r["M"] = float(r["M"])
    r["season"] = int(r["season"])
    r["xG90"] = float(r["xG"]) / r["M"]
    r["xGA90"] = float(r["xGA"]) / r["M"]

NOMS_FR = {"EPL": "Premier League", "La_Liga": "Liga", "Bundesliga": "Bundesliga",
           "Ligue_1": "Ligue 1", "Serie_A": "Serie A"}
AFFICHAGE = {
    "Paris Saint Germain": "Paris SG", "RasenBallsport Leipzig": "RB Leipzig",
    "Wolverhampton Wanderers": "Wolves", "Parma Calcio 1913": "Parme",
    "AC Milan": "Milan AC", "VfB Stuttgart": "Stuttgart", "FC Cologne": "Cologne",
    "Atletico Madrid": "Atlético Madrid", "Bayer Leverkusen": "Leverkusen",
    "Borussia M.Gladbach": "Mönchengladbach", "Eintracht Frankfurt": "Francfort",
    "Nottingham Forest": "Nott. Forest", "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle", "Athletic Club": "Athletic Bilbao",
    "Real Betis": "Betis Séville",
}

DATA = {}
for lg in NOMS_FR:
    grp = [r for r in rows if r["league"] == lg and r["season"] == 2025]
    if not grp:
        continue
    n = sum(r["M"] for r in grp) / len(grp)
    DATA[lg] = {"nom": NOMS_FR[lg], "n": round(n, 1), "eq": sorted(
        [[r["team"], round(r["xG90"], 4), round(r["xGA90"], 4)] for r in grp])}

data_json = json.dumps(DATA, ensure_ascii=False)
aff_json = json.dumps(AFFICHAGE, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analyseur de match - xG / xGA (hors-ligne)</title>
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
.regle{font-size:14px;color:#3b424d}
.regle li{margin-bottom:6px}
details{margin-top:8px}
summary{cursor:pointer;font-weight:600;font-size:14px;color:#0f766e}
.note{font-size:12px;color:#7b8492;margin-top:6px}
.err{color:var(--rouge);font-weight:600;margin-top:10px}
</style></head><body><div class="wrap">
<h1>Analyseur de match <span class="note">(hors-ligne)</span></h1>
<p class="sous">Vous choisissez deux équipes, l'outil dit qui gagne le plus souvent
et si la cote de votre bookmaker vaut le coup. Fonctionne sans internet, sans serveur.</p>

<div class="carte">
  <label>1. Les deux équipes</label>
  <div class="grid2">
    <select id="home"><option value="">Équipe à domicile</option></select>
    <select id="away"><option value="">Équipe à l'extérieur</option></select>
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
  <details><summary>J'ai des chiffres plus récents (mode manuel)</summary>
    <p class="note">Si vous avez les xG des 5-10 derniers matchs (Understat, FBref),
    entrez-les ici en buts par match. L'outil tient compte de la taille de l'échantillon.</p>
    <label>Nombre de matchs pris en compte</label>
    <input id="mn" type="number" value="10" min="3" max="38">
    <div class="grid2">
      <div><label class="note">xG/match - domicile</label><input id="mxg_h" type="number" step="0.01" placeholder="1,80"></div>
      <div><label class="note">xG/match - extérieur</label><input id="mxg_a" type="number" step="0.01" placeholder="1,40"></div>
      <div><label class="note">xG concédés/match - domicile</label><input id="mxga_h" type="number" step="0.01" placeholder="1,10"></div>
      <div><label class="note">xG concédés/match - extérieur</label><input id="mxga_a" type="number" step="0.01" placeholder="1,30"></div>
    </div>
  </details>
</div>

<div id="out"></div>

<div class="carte">
  <b>Les 4 règles à retenir</b>
  <ul class="regle">
    <li><b>Jouez seulement si la cote proposée dépasse la cote juste de 5 %.</b> En dessous, c'est du bruit.</li>
    <li><b>Mise : 1 à 2 % de votre bankroll</b> (l'outil donne le chiffre exact, base 1/4 de Kelly).</li>
    <li><b>Ne jugez jamais une défense sur 5 matchs.</b> C'est le signal le plus trompeur :
    sur 5 matchs il ne compte que pour 13 %.</li>
    <li><b>Sur « ne pas perdre » (1X, X2), la défense compte autant que l'attaque.</b>
    Sur « qui gagne », c'est l'attaque qui décide.</li>
  </ul>
</div>
</div>

<script id="modele">
// ---------------------------------------------------------------------------
// MODELE - portage fidele de modele_xg.py (memes constantes, memes calculs)
// ---------------------------------------------------------------------------
const K=0.915,HFA=1.12,RHO_ATT=0.783,RHO_DEF=0.526,N_REF=38,MAXG=12;
const DATA=__DATA__;
const AFFICHAGE=__AFFICHAGE__;
function nom(t){return AFFICHAGE[t]||t;}
function mean(a){let s=0;for(const v of a)s+=v;return s/a.length;}
function fiab(n,rho){if(n<=0)return 0;const r=rho/(1-rho);return (r*n)/(r*n+N_REF);}
const _f={};function fact(i){if(_f[i]!==undefined)return _f[i];let r=1;for(let k=2;k<=i;k++)r*=k;return _f[i]=r;}
function ratingsLigue(lg){
  const eq=DATA[lg].eq,n=DATA[lg].n;
  const wa=fiab(n,RHO_ATT),wd=fiab(n,RHO_DEF);
  const mu=mean(eq.map(e=>e[1]));
  const A={},D={};
  for(const e of eq){A[e[0]]=Math.pow(e[1]/mu,wa);D[e[0]]=Math.pow(e[2]/mu,wd);}
  const ma=mean(Object.values(A)),md=mean(Object.values(D));
  for(const t in A){A[t]/=ma;D[t]/=md;}
  return {mu,A,D,wa,wd};
}
function lambdas(home,away,mu,A,D){
  const ah=A[home]??1,da=D[away]??1,aa=A[away]??1,dh=D[home]??1;
  return [K*mu*ah*da*HFA,K*mu*aa*dh/HFA];
}
function pois(l){const v=[];for(let i=0;i<=MAXG;i++)v.push(Math.exp(-l)*Math.pow(l,i)/fact(i));return v;}
function grille(lh,la){
  const ph=pois(lh),pa=pois(la),m=[];
  for(let i=0;i<=MAXG;i++){const r=[];for(let j=0;j<=MAXG;j++)r.push(ph[i]*pa[j]);m.push(r);}
  let tot=0;for(const r of m)for(const c of r)tot+=c;
  return m.map(r=>r.map(c=>c/tot));
}
function probas(lh,la){
  const m=grille(lh,la);let p1=0,px=0,p2=0;
  for(let i=0;i<=MAXG;i++){for(let j=0;j<i;j++)p1+=m[i][j];px+=m[i][i];for(let j=i+1;j<=MAXG;j++)p2+=m[i][j];}
  return [p1,px,p2];
}
function buts(lh,la){
  const m=grille(lh,la);
  let o25=0,btts=0;
  for(let i=0;i<=MAXG;i++)for(let j=0;j<=MAXG;j++){if(i+j>2.5)o25+=m[i][j];if(i>=1&&j>=1)btts+=m[i][j];}
  return {over25:o25,btts};
}
function value(p,c){return p*c-1;}
function kelly(p,c){const b=c-1;if(b<=0)return 0;return Math.max(0,(p*b-(1-p))/b)*0.25;}
function forceEnMots(v,sens){
  const e=100*(v-1);
  if(Math.abs(e)<4)return "dans la moyenne";
  let mot;
  if(sens==="att"){
    mot=e>=25?"excellente":e>=12?"très bonne":e>0?"correcte":e>-12?"faible":e>-25?"très faible":"catastrophique";
    return mot+" ("+(e>0?"+":"")+e.toFixed(0)+" % de xG créés)";
  }else{
    mot=e>=25?"catastrophique":e>=12?"très fragile":e>0?"fragile":e>-12?"solide":e>-25?"très solide":"excellente";
    return mot+" ("+(e>0?"+":"")+e.toFixed(0)+" % de xG concédés)";
  }
}
function pct(x){return Math.round(100*x*10)/10;}
function analyse(home,away,cotes,lg,manuel){
  let mu,A,D,wa,wd,source,poids,brut;
  if(manuel){
    mu=DATA[lg]?ratingsLigue(lg).mu:1.55;
    const n=manuel.n;
    wa=fiab(n,RHO_ATT);wd=fiab(n,RHO_DEF);
    A={};D={};
    A[home]=Math.pow(manuel.xg_h/mu,wa);A[away]=Math.pow(manuel.xg_a/mu,wa);
    D[home]=Math.pow(manuel.xga_h/mu,wd);D[away]=Math.pow(manuel.xga_a/mu,wd);
    brut={};
    brut[home+",a"]=manuel.xg_h/mu;brut[away+",a"]=manuel.xg_a/mu;
    brut[home+",d"]=manuel.xga_h/mu;brut[away+",d"]=manuel.xga_a/mu;
    source="saisie manuelle sur "+Math.round(n)+" derniers matchs";
    poids="crédit accordé à l'attaque : "+Math.round(wa*100)+" % · à la défense : "+Math.round(wd*100)+" % (échantillon de "+Math.round(n)+" matchs)";
  }else{
    const r=ratingsLigue(lg);
    mu=r.mu;A=r.A;D=r.D;wa=r.wa;wd=r.wd;
    brut={};
    for(const e of DATA[lg].eq){brut[e[0]+",a"]=e[1]/mu;brut[e[0]+",d"]=e[2]/mu;}
    source="saison 2025/2026 complète ("+DATA[lg].nom+")";
    poids="crédit accordé à l'attaque : "+Math.round(wa*100)+" % · à la défense : "+Math.round(wd*100)+" % (saison complète)";
  }
  const hn=nom(home),an=nom(away);
  const [lh,la]=lambdas(home,away,mu,A,D);
  const [p1,px,p2]=probas(lh,la);
  const b=buts(lh,la);
  const marches=[
    ["1","Victoire "+hn,p1],["X","Match nul",px],["2","Victoire "+an,p2],
    ["1X",hn+" ne perd pas",p1+px],["X2",an+" ne perd pas",px+p2],
    ["O25","Plus de 2,5 buts",b.over25],["U25","Moins de 2,5 buts",1-b.over25],
    ["BTTS","Les deux équipes marquent",b.btts]];
  const out_m=[],verdicts=[];
  for(const [code,lib,p] of marches){
    const cote=cotes[code];
    const ligne={code,libelle:lib,p:pct(p),cote_juste:Math.round(100/p)/100};
    if(cote&&cote>1){
      const edge=value(p,cote),mise=kelly(p,cote);
      ligne.cote=cote;ligne.edge=Math.round(edge*1000)/10||0;ligne.mise=Math.round(mise*10000)/100;
      if(edge>0)verdicts.push([edge,lib,p,cote,mise]);
    }
    out_m.push(ligne);
  }
  const saisies=out_m.filter(l=>"cote" in l);
  let niveau,couleur,phrase,conseil;
  verdicts.sort((a,b2)=>b2[0]-a[0]);
  if(!saisies.length){
    niveau="INFO";couleur="gris";
    phrase="Voici les probabilités. Entrez les cotes de votre bookmaker pour savoir s'il y a de la valeur.";
    conseil="";
  }else if(verdicts.length&&verdicts[0][0]>0){
    const [edge,lib,p,cote,mise]=verdicts[0];
    if(edge>=0.15){niveau="AVANTAGE SUSPECT";couleur="orange";
      phrase="Cote "+fmt(cote)+" sur « "+lib+" » (juste : "+(1/p).toFixed(2)+"), avantage "+Math.round(edge*100)+" %. Un avantage aussi gros n'existe presque jamais : vérifiez d'abord vos chiffres (blessés, compos, xG récents).";}
    else if(edge>=0.05){niveau="BONNE COTE";couleur="vert";
      phrase="Le bookmaker offre "+fmt(cote)+" sur « "+lib+" » alors que la cote juste est "+(1/p).toFixed(2)+". Avantage de "+(edge*100).toFixed(1)+" %.";}
    else if(edge>=0.02){niveau="LEGER AVANTAGE";couleur="orange";
      phrase="Cote "+fmt(cote)+" sur « "+lib+" » (juste : "+(1/p).toFixed(2)+"). Avantage faible : "+(edge*100).toFixed(1)+" %. Dans le bruit.";}
    else{niveau="PAS DE VALEUR";couleur="rouge";
      phrase="La meilleure de vos cotes est "+fmt(cote)+" sur « "+lib+" » (juste : "+(1/p).toFixed(2)+") : avantage "+(edge*100).toFixed(1)+" %, trop faible pour jouer.";}
    conseil=mise>0?"Mise conseillée : "+(mise*100).toFixed(1)+" € pour 100 € de bankroll (soit 1/4 de Kelly).":"Pas de mise : l'avantage est nul ou négatif.";
  }else{
    const meil=saisies.reduce((m,l)=>l.edge>m.edge?l:m);
    niveau="PAS DE VALEUR";couleur="rouge";
    phrase="Aucune de vos cotes ne bat la cote juste. La moins mauvaise : "+fmt(meil.cote)+" sur « "+meil.libelle+" » (juste : "+meil.cote_juste+", soit "+(meil.edge>=0?"+":"")+meil.edge.toFixed(1)+" %). Ne jouez pas ce match.";
    conseil="Pas de mise.";
  }
  return {home:hn,away:an,ligue:DATA[lg]?DATA[lg].nom:lg,source,poids,
    buts_home:Math.round(lh*100)/100,buts_away:Math.round(la*100)/100,buts_total:Math.round((lh+la)*100)/100,
    att_home:forceEnMots(brut[home+",a"],"att"),def_home:forceEnMots(brut[home+",d"],"def"),
    att_away:forceEnMots(brut[away+",a"],"att"),def_away:forceEnMots(brut[away+",d"],"def"),
    p1:pct(p1),px:pct(px),p2:pct(p2),
    cote1:Math.round(100/p1)/100,cotex:Math.round(100/px)/100,cote2:Math.round(100/p2)/100,
    marches:out_m,niveau,couleur,phrase,conseil};
}
function fmt(x){return String(Math.round(x*100)/100);}
</script>

<script>
const HOME=document.getElementById('home'),AWAY=document.getElementById('away'),OUT=document.getElementById('out');
for(const lg in DATA){
  for(const sel of [HOME,AWAY]){
    const og=document.createElement('optgroup');og.label=DATA[lg].nom;
    for(const e of DATA[lg].eq){const o=document.createElement('option');o.value=lg+'|'+e[0];o.textContent=nom(e[0]);og.appendChild(o);}
    sel.appendChild(og);
  }
}
HOME.value='EPL|Arsenal';AWAY.value='EPL|Manchester City';
function num(id){const v=parseFloat(document.getElementById(id).value.replace(',','.'));return isFinite(v)&&v>1?v:null;}
function f2(x){return x.toFixed(2).replace('.',',');}
function go(){
  const h=HOME.value.split('|'),a=AWAY.value.split('|');
  if(!h[1]||!a[1]){OUT.innerHTML='<p class="err">Choisissez les deux équipes.</p>';return;}
  if(h[1]===a[1]){OUT.innerHTML='<p class="err">Les deux équipes doivent être différentes.</p>';return;}
  const cotes={},map={c1:'1',cx:'X',c2:'2',c1X:'1X',cO:'O25',cB:'BTTS'};
  for(const k in map){const v=num(k);if(v)cotes[map[k]]=v;}
  let manuel=null;
  const n=parseFloat(document.getElementById('mn').value);
  const q=['mxg_h','mxg_a','mxga_h','mxga_a'].map(num);
  if(q.every(x=>x))manuel={n:n||10,xg_h:q[0],xg_a:q[1],xga_h:q[2],xga_a:q[3]};
  const d=analyse(h[1],a[1],cotes,h[0],manuel);
  let html='<div class="verdict '+d.couleur+'"><b>'+d.niveau+'</b>'+d.phrase
    +(d.conseil?'<br><b style="font-size:17px;margin-top:8px">'+d.conseil+'</b>':'')+'</div>';
  html+='<div class="carte"><b>'+d.home+' &nbsp;-&nbsp; '+d.away+'</b>'
    +'<div class="note">'+d.source+' &middot; '+d.poids+'</div>'
    +'<div class="buts" style="margin-top:12px">'
    +'<div><div class="v">'+f2(d.buts_home)+'</div><div class="l">buts attendus<br>'+d.home+'</div></div>'
    +'<div><div class="v">'+f2(d.buts_total)+'</div><div class="l">buts attendus<br>au total</div></div>'
    +'<div><div class="v">'+f2(d.buts_away)+'</div><div class="l">buts attendus<br>'+d.away+'</div></div>'
    +'</div>'
    +'<div class="chances">'
    +'<div class="chance"><div class="v">'+d.p1+'%</div><div class="l">victoire '+d.home+'</div><div class="c">cote juste '+f2(d.cote1)+'</div></div>'
    +'<div class="chance"><div class="v">'+d.px+'%</div><div class="l">match nul</div><div class="c">cote juste '+f2(d.cotex)+'</div></div>'
    +'<div class="chance"><div class="v">'+d.p2+'%</div><div class="l">victoire '+d.away+'</div><div class="c">cote juste '+f2(d.cote2)+'</div></div>'
    +'</div></div>';
  html+='<div class="carte"><b>Lecture des deux équipes</b><table>'
    +'<tr><th></th><th>Attaque</th><th>Défense</th></tr>'
    +'<tr><td>'+d.home+'</td><td>'+d.att_home+'</td><td>'+d.def_home+'</td></tr>'
    +'<tr><td>'+d.away+'</td><td>'+d.att_away+'</td><td>'+d.def_away+'</td></tr></table></div>';
  html+='<div class="carte"><b>Tous les marchés</b><table>'
    +'<tr><th>Marché</th><th class="n">Prob.</th><th class="n">Cote juste</th><th class="n">Cote</th><th class="n">Avantage</th><th class="n">Mise</th></tr>';
  for(const m of d.marches){
    const e=(m.edge!==undefined)?'<span class="'+(m.edge>=5?'ok':(m.edge>=2?'':'ko'))+'">'+(m.edge>0?'+':'')+String(m.edge).replace('.',',')+'%</span>':'<span class="ko">-</span>';
    html+='<tr><td>'+m.libelle+'</td><td class="n">'+m.p+'%</td><td class="n">'+f2(m.cote_juste)+'</td><td class="n">'+(m.cote?f2(m.cote):'-')+'</td><td class="n">'+e+'</td><td class="n">'+(m.mise?String(m.mise).replace('.',',')+'%':'-')+'</td></tr>';
  }
  html+='</table><div class="note">« Avantage » = ce que la cote proposée rapporte de plus que la cote juste. Mise = part de votre bankroll (1/4 de Kelly).</div></div>';
  OUT.innerHTML=html;
}
</script></body></html>
"""

html = TEMPLATE.replace("__DATA__", data_json).replace("__AFFICHAGE__", aff_json)
open("analyseur.html", "w", encoding="utf-8").write(html)
print("analyseur.html écrit :", len(html), "octets ; ligues :", ", ".join(DATA))
