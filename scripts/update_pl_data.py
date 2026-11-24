#!/usr/bin/env python3
"""
Met à jour data/pl-2026-27.json avec les statistiques officielles de la Premier League.

Sources (dans l'ordre) :
  1. API officielle Fantasy Premier League — bootstrap-static + fixtures
     -> totaux, splits Domicile/Extérieur exacts, forme, calendrier à venir.
  2. API publique ESPN — standings + scoreboard (secours)
     -> totaux uniquement ; les splits Dom/Ext sont conservés depuis l'instantané
        précédent lorsqu'ils existent.

Aucune dépendance externe : Python 3 standard uniquement (urllib / json).
Exécuté par .github/workflows/update-pl-data.yml toutes les 6 h et à la demande.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "data" / "pl-2026-27.json"
SEASON = "2026-27"
UA = (
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"
)

FPL_BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_FIXTURES = "https://fantasy.premierleague.com/api/fixtures/"
ESPN_STANDINGS = "https://site.web.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
ESPN_SCOREBOARD = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"

# Nom FPL -> (identifiant stable, nom complet)
CANON = {
    "arsenal": ("arsenal", "Arsenal"),
    "aston-villa": ("aston-villa", "Aston Villa"),
    "bournemouth": ("bournemouth", "AFC Bournemouth"),
    "afc-bournemouth": ("bournemouth", "AFC Bournemouth"),
    "brentford": ("brentford", "Brentford"),
    "brighton": ("brighton", "Brighton & Hove Albion"),
    "burnley": ("burnley", "Burnley"),
    "chelsea": ("chelsea", "Chelsea"),
    "coventry": ("coventry", "Coventry City"),
    "coventry-city": ("coventry", "Coventry City"),
    "crystal-palace": ("crystal-palace", "Crystal Palace"),
    "everton": ("everton", "Everton"),
    "fulham": ("fulham", "Fulham"),
    "hull": ("hull", "Hull City"),
    "hull-city": ("hull", "Hull City"),
    "ipswich": ("ipswich", "Ipswich Town"),
    "leeds": ("leeds", "Leeds United"),
    "leicester": ("leicester", "Leicester City"),
    "liverpool": ("liverpool", "Liverpool"),
    "man-city": ("man-city", "Manchester City"),
    "man-utd": ("man-utd", "Manchester United"),
    "manchester-city": ("man-city", "Manchester City"),
    "manchester-united": ("man-utd", "Manchester United"),
    "newcastle": ("newcastle", "Newcastle United"),
    "nott-m-forest": ("nottingham-forest", "Nottingham Forest"),
    "nottingham-forest": ("nottingham-forest", "Nottingham Forest"),
    "sheffield-utd": ("sheffield-utd", "Sheffield United"),
    "southampton": ("southampton", "Southampton"),
    "spurs": ("tottenham", "Tottenham Hotspur"),
    "tottenham": ("tottenham", "Tottenham Hotspur"),
    "sunderland": ("sunderland", "Sunderland"),
    "west-ham": ("west-ham", "West Ham United"),
    "wolves": ("wolves", "Wolverhampton Wanderers"),
    "wolverhampton-wanderers": ("wolves", "Wolverhampton Wanderers"),
}


def slugify(name: str) -> str:
    out = name.lower().replace("&", "and").replace(".", "").replace("'", "")
    out = "".join(ch if (ch.isalnum() or ch == " ") else "-" for ch in out)
    out = "-".join(part for part in out.split() if part)
    return out


def canonical(name: str) -> tuple[str, str]:
    """Retourne (id stable, nom complet) pour un nom de club quelconque."""
    key = slugify(name)
    if key in CANON:
        return CANON[key]
    # tolérance : "Man Utd" / "Manchester United" / "Nott'm Forest"
    for k, v in CANON.items():
        if key == k or key in k or k in key:
            return v
    return key, name


def fetch_json(url: str, timeout: int = 30):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def zero_line() -> dict:
    return {"mp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}


def _future_fixtures(previous: dict) -> list:
    """Conserve le calendrier précédent s'il est encore d'actualité."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [f for f in previous.get("fixtures", []) if (f.get("date") or "") >= today][:20]


def read_previous() -> dict:
    try:
        return json.loads(OUT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# --------------------------------------------------------------------------
# Source 1 — Fantasy Premier League
# --------------------------------------------------------------------------
def update_from_fpl(previous: dict) -> dict:
    boot = fetch_json(FPL_BOOTSTRAP)
    fixtures = fetch_json(FPL_FIXTURES)
    if not boot.get("teams"):
        raise RuntimeError("bootstrap-static sans équipes")

    teams: dict[int, dict] = {}
    for t in boot["teams"]:
        tid, full = canonical(t.get("name") or t.get("short_name") or "?")
        teams[t["id"]] = {
            "fpl_id": t["id"],
            "id": tid,
            "name": full,
            "short": (t.get("short_name") or full[:3]).upper(),
            "pos": 0,
            **zero_line(),
            "home": zero_line(),
            "away": zero_line(),
            "results": [],
        }

    upcoming: list[dict] = []
    last_finished_gw = 0
    last_finished_event_id = 0
    finished_count = 0

    def kickoff_key(fx: dict) -> tuple:
        return (fx.get("kickoff_time") or "9999-12-31", fx.get("id") or 0)

    for fx in sorted(fixtures, key=kickoff_key):
        th, ta = fx.get("team_h"), fx.get("team_a")
        if th not in teams or ta not in teams:
            continue
        H, A = teams[th], teams[ta]
        hg, ag = fx.get("team_h_score"), fx.get("team_a_score")
        done = bool(fx.get("finished") or fx.get("finished_provisional"))
        event_id = fx.get("event") or 0

        if done and hg is not None and ag is not None:
            hg, ag = int(hg), int(ag)
            finished_count += 1
            if event_id:
                last_finished_event_id = max(last_finished_event_id, event_id)

            # domicile
            H["mp"] += 1; H["gf"] += hg; H["ga"] += ag
            H["home"]["mp"] += 1; H["home"]["gf"] += hg; H["home"]["ga"] += ag
            # extérieur
            A["mp"] += 1; A["gf"] += ag; A["ga"] += hg
            A["away"]["mp"] += 1; A["away"]["gf"] += ag; A["away"]["ga"] += hg

            if hg > ag:
                H["w"] += 1; H["pts"] += 3; H["home"]["w"] += 1; H["home"]["pts"] += 3
                A["l"] += 1; A["away"]["l"] += 1
                H["results"].append("W"); A["results"].append("L")
            elif hg < ag:
                A["w"] += 1; A["pts"] += 3; A["away"]["w"] += 1; A["away"]["pts"] += 3
                H["l"] += 1; H["home"]["l"] += 1
                H["results"].append("L"); A["results"].append("W")
            else:
                H["d"] += 1; H["pts"] += 1; H["home"]["d"] += 1; H["home"]["pts"] += 1
                A["d"] += 1; A["pts"] += 1; A["away"]["d"] += 1; A["away"]["pts"] += 1
                H["results"].append("D"); A["results"].append("D")
        elif not done:
            ko = fx.get("kickoff_time")
            if not ko:
                continue
            upcoming.append({
                "date": ko[:10],
                "time": ko[11:16],
                "round": f"J{event_id}" if event_id else "PL",
                "home": H["name"],
                "away": A["name"],
            })

    if len(teams) < 20:
        raise RuntimeError(f"seulement {len(teams)} équipes FPL")
    if all(t["mp"] == 0 for t in teams.values()):
        raise RuntimeError("table FPL vide")

    # journée réellement jouée = max des journées terminées
    for fx in fixtures:
        if (fx.get("finished") or fx.get("finished_provisional")) and fx.get("event"):
            last_finished_gw = max(last_finished_gw, int(fx["event"]))
    if last_finished_gw == 0:
        last_finished_gw = max((t["mp"] for t in teams.values()), default=0)

    ordered = sorted(
        teams.values(),
        key=lambda t: (-t["pts"], -(t["gf"] - t["ga"]), -t["gf"], t["name"]),
    )
    out_teams = []
    for idx, t in enumerate(ordered, start=1):
        out_teams.append({
            "id": t["id"],
            "name": t["name"],
            "short": t["short"],
            "pos": idx,
            "mp": t["mp"], "w": t["w"], "d": t["d"], "l": t["l"],
            "gf": t["gf"], "ga": t["ga"], "pts": t["pts"],
            "home": t["home"],
            "away": t["away"],
            "form": "".join(t["results"][-5:]),
        })

    return {
        "season": SEASON,
        "league": "Premier League",
        "slug": "eng.1",
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matchday": last_finished_gw,
        "source": f"Fantasy Premier League officiel (J{last_finished_gw})",
        "matchesPlayed": finished_count,
        "teams": out_teams,
        "fixtures": upcoming[:20] or _future_fixtures(previous),
    }


# --------------------------------------------------------------------------
# Source 2 — ESPN (secours, totaux sans splits)
# --------------------------------------------------------------------------
def update_from_espn(previous: dict) -> dict:
    standings = fetch_json(ESPN_STANDINGS)
    try:
        board = fetch_json(ESPN_SCOREBOARD)
    except Exception:
        board = {}

    entries = (
        standings.get("children", [{}])[0].get("standings", {}).get("entries")
        or standings.get("standings", {}).get("entries")
        or []
    )
    if len(entries) < 18:
        raise RuntimeError(f"ESPN n'a renvoyé que {len(entries)} équipes")

    prev_by_id = {t.get("id"): t for t in previous.get("teams", []) if isinstance(t, dict)}

    def val(stats, name, default=0):
        for s in stats:
            if s.get("name") == name:
                v = s.get("value")
                if v is None:
                    return default
                return int(round(float(v)))
        return default

    out_teams = []
    max_mp = 0
    for e in entries:
        tm = e.get("team", {})
        stats = e.get("stats", [])
        name = tm.get("displayName") or tm.get("name") or "?"
        tid, full = canonical(name)
        mp = val(stats, "gamesPlayed")
        w = val(stats, "wins")
        d = val(stats, "ties")
        l = val(stats, "losses")
        gf = val(stats, "pointsFor")
        ga = val(stats, "pointsAgainst")
        pts = val(stats, "points", w * 3 + d)
        max_mp = max(max_mp, mp)

        prev = prev_by_id.get(tid)
        home = prev.get("home") if prev else None
        away = prev.get("away") if prev else None
        splits_ok = bool(prev and prev.get("mp") == mp and home and away)

        if not splits_ok:
            # splits inconnus : estimation proportionnelle (marquée comme telle)
            if prev and prev.get("mp"):
                k = mp / prev["mp"]
                home = {kk: int(round(vv * k)) for kk, vv in prev["home"].items()}
                away = {kk: int(round(vv * k)) for kk, vv in prev["away"].items()}
            else:
                half = max(1, mp // 2)
                home = {"mp": half, "w": 0, "d": 0, "l": 0,
                        "gf": int(round(gf * 0.55)), "ga": int(round(ga * 0.45)), "pts": 0}
                away = {"mp": max(1, mp - half), "w": 0, "d": 0, "l": 0,
                        "gf": int(round(gf * 0.45)), "ga": int(round(ga * 0.55)), "pts": 0}

        out_teams.append({
            "id": tid,
            "name": full if prev is None else prev.get("name", full),
            "short": tm.get("abbreviation") or full[:3].upper(),
            "pos": 0,
            "mp": mp, "w": w, "d": d, "l": l,
            "gf": gf, "ga": ga, "pts": pts,
            "home": home,
            "away": away,
            "form": (prev or {}).get("form", ""),
            "splitsEstimated": not splits_ok,
        })

    out_teams.sort(key=lambda t: (-t["pts"], -(t["gf"] - t["ga"]), -t["gf"], t["name"]))
    for i, t in enumerate(out_teams, start=1):
        t["pos"] = i

    upcoming = []
    for ev in (board.get("events") or []):
        comp = (ev.get("competitions") or [{}])[0]
        state = ((comp.get("status") or {}).get("type") or {}).get("state")
        if state == "post":
            continue
        cs = comp.get("competitors") or []
        home = next((c for c in cs if c.get("homeAway") == "home"), None)
        away = next((c for c in cs if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        dt = ev.get("date") or ""
        upcoming.append({
            "date": dt[:10],
            "time": dt[11:16] if len(dt) >= 16 else "",
            "round": f"J{max_mp + 1}",
            "home": (home.get("team") or {}).get("displayName", ""),
            "away": (away.get("team") or {}).get("displayName", ""),
        })

    return {
        "season": SEASON,
        "league": "Premier League",
        "slug": "eng.1",
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matchday": max_mp,
        "source": f"ESPN (J{max_mp})",
        "matchesPlayed": sum(t["mp"] for t in out_teams) // 2,
        "teams": out_teams,
        "fixtures": (upcoming or previous.get("fixtures", []))[:20],
    }


# --------------------------------------------------------------------------
def sanity_check(data: dict) -> None:
    teams = data.get("teams", [])
    if len(teams) < 18:
        raise RuntimeError(f"instantané invalide : {len(teams)} équipes")
    mps = {t["mp"] for t in teams}
    if len(mps) > 3:
        raise RuntimeError(f"incohérence de matchs joués : {sorted(mps)}")
    total_gf = sum(t["gf"] for t in teams)
    total_ga = sum(t["ga"] for t in teams)
    if total_gf != total_ga:
        raise RuntimeError(f"buts marqués ({total_gf}) != buts encaissés ({total_ga})")


def main() -> int:
    previous = read_previous()
    data = None
    errors = []

    for label, fn in (("FPL", update_from_fpl), ("ESPN", update_from_espn)):
        try:
            candidate = fn(previous)
            sanity_check(candidate)
            data = candidate
            print(f"[OK] {label} : {len(data['teams'])} équipes, J{data['matchday']}, "
                  f"{data.get('matchesPlayed', '?')} matchs.")
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
            print(f"[WARN] Échec {label} : {exc}", file=sys.stderr)

    if data is None:
        print("[ERROR] Aucune source disponible : " + " | ".join(errors), file=sys.stderr)
        return 1

    # on garde les instantanés identiques -> pas de commit inutile
    old = previous.get("teams")
    new = data.get("teams")
    if old == new and previous.get("fixtures") == data.get("fixtures"):
        print("[INFO] Aucun changement — fichier inchangé.")
        return 0

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Écrit : {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
