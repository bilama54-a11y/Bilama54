#!/usr/bin/env python3
"""
Met à jour data/ucl-2026-27.json — UEFA Champions League 2026-27, League Phase (36 clubs).

Source unique : API publique ESPN (aucune clé requise)
  1. /apis/v2/sports/soccer/uefa.champions/standings       -> classement officiel (totaux)
  2. /apis/site/v2/sports/soccer/uefa.champions/scoreboard -> résultats match par match,
     agrégés pour reconstruire les splits Domicile / Extérieur exacts,
     et calendrier des rencontres à venir.

Le script conserve le calendrier déjà publié (les 8 journées sont fixées à l'avance) :
une affiche qui apparaît dans les résultats est simplement retirée de la liste « à venir ».

Exécuté par .github/workflows/update-ucl-data.yml (toutes les 6 h + à la demande).
"""

from __future__ import annotations

import json
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "data" / "ucl-2026-27.json"

LEAGUE = "uefa.champions"
ESPN_BASE = "https://site.web.api.espn.com/apis"
STANDINGS_URL = f"{ESPN_BASE}/v2/sports/soccer/{LEAGUE}/standings"
SCOREBOARD_URL = f"{ESPN_BASE}/site/v2/sports/soccer/{LEAGUE}/scoreboard"

UA = (
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"
)

# Alias connus (nom ESPN normalisé -> identifiant du fichier de données)
ALIASES = {
    "bodo glimt": "bodo-glimt",
    "bodoglimt": "bodo-glimt",
    "lask linz": "lask",
    "lask": "lask",
    "inter": "inter-milan",
    "inter milan": "inter-milan",
    "bayern munchen": "bayern-munich",
    "bayern munich": "bayern-munich",
    "manchester city": "manchester-city",
    "manchester united": "manchester-united",
    "paris saint germain": "paris-saint-germain",
    "psg": "paris-saint-germain",
    "atletico madrid": "atletico-madrid",
    "atletico de madrid": "atletico-madrid",
    "sporting": "sporting-cp",
    "sporting lisbon": "sporting-cp",
    "sporting cp": "sporting-cp",
    "stuttgart": "stuttgart",
    "vfb stuttgart": "stuttgart",
    "club brugge": "club-brugge",
    "brugge": "club-brugge",
    "fenerbahce": "fenerbahce",
    "slavia prague": "slavia-prague",
    "slovan bratislava": "slovan-bratislava",
    "shakhtar donetsk": "shakhtar-donetsk",
    "aek athens": "aek-athens",
    "aek": "aek-athens",
    "psv": "psv-eindhoven",
    "psv eindhoven": "psv-eindhoven",
    "rb leipzig": "rb-leipzig",
    "real betis": "real-betis",
    "real madrid": "real-madrid",
    "villarreal": "villarreal",
    "roma": "roma",
    "napoli": "napoli",
    "lens": "lens",
    "lille": "lille",
    "como": "como",
    "viking": "viking",
    "sabah": "sabah",
    "galatasaray": "galatasaray",
    "feyenoord": "feyenoord",
    "porto": "porto",
    "benfica": "benfica",
    "arsenal": "arsenal",
    "aston villa": "aston-villa",
    "liverpool": "liverpool",
    "barcelona": "barcelona",
    "borussia dortmund": "borussia-dortmund",
    "dortmund": "borussia-dortmund",
}

# Fenêtres de dates couvrant la League Phase (8 septembre 2026 -> 27 janvier 2027)
WINDOW_START = date(2026, 9, 1)
WINDOW_END = date(2027, 1, 31)


def norm(name: str) -> str:
    s = unicodedata.normalize("NFD", name or "").encode("ascii", "ignore").decode()
    s = "".join(ch if ch.isalnum() else " " for ch in s.lower())
    return " ".join(s.split())


def slugify(name: str) -> str:
    return norm(name).replace(" ", "-")


def fetch_json(url: str, timeout: int = 30):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def empty_line() -> dict:
    return {"mp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}


def read_previous() -> dict:
    try:
        return json.loads(OUT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def stat(stats: list, name: str, default=0):
    for s in stats:
        if s.get("name") == name:
            v = s.get("value")
            return default if v is None else int(round(float(v)))
    return default


# ---------------------------------------------------------------------------
# 1. Classement ESPN (totaux officiels)
# ---------------------------------------------------------------------------
def fetch_standings() -> list[dict]:
    data = fetch_json(STANDINGS_URL)
    entries = (
        data.get("children", [{}])[0].get("standings", {}).get("entries")
        or data.get("standings", {}).get("entries")
        or []
    )
    if len(entries) < 30:
        raise RuntimeError(f"ESPN standings : {len(entries)} équipes seulement")

    out = []
    for e in entries:
        tm = e.get("team", {})
        st = e.get("stats", [])
        out.append({
            "espnId": str(tm.get("id") or ""),
            "name": tm.get("displayName") or tm.get("name") or "?",
            "short": (tm.get("abbreviation") or "")[:4].upper(),
            "mp": stat(st, "gamesPlayed"),
            "w": stat(st, "wins"),
            "d": stat(st, "ties"),
            "l": stat(st, "losses"),
            "gf": stat(st, "pointsFor"),
            "ga": stat(st, "pointsAgainst"),
            "pts": stat(st, "points"),
        })
    return out


# ---------------------------------------------------------------------------
# 2. Résultats match par match (splits Dom/Ext + calendrier)
# ---------------------------------------------------------------------------
def fetch_results() -> list[dict]:
    """Balaye la League Phase par fenêtres de 12 jours et renvoie les matchs."""
    events: dict[str, dict] = {}
    day = WINDOW_START
    while day <= WINDOW_END:
        end = min(day + timedelta(days=11), WINDOW_END)
        url = f"{SCOREBOARD_URL}?dates={day:%Y%m%d}-{end:%Y%m%d}&limit=500"
        try:
            payload = fetch_json(url, timeout=35)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] scoreboard {day}->{end} : {exc}", file=sys.stderr)
            day = end + timedelta(days=1)
            continue
        for ev in payload.get("events", []) or []:
            comp = (ev.get("competitions") or [{}])[0]
            comps = comp.get("competitors") or []
            home = next((c for c in comps if c.get("homeAway") == "home"), None)
            away = next((c for c in comps if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue
            eid = str(ev.get("id") or comp.get("id") or "")
            if not eid:
                continue
            state = ((comp.get("status") or {}).get("type") or {}).get("state", "pre")
            season_type = ((ev.get("season") or {}).get("type"))
            events[eid] = {
                "id": eid,
                "date": (ev.get("date") or "")[:10],
                "time": (ev.get("date") or "")[11:16],
                "state": state,  # pre | in | post
                "seasonType": season_type,
                "home": (home.get("team") or {}).get("displayName", ""),
                "away": (away.get("team") or {}).get("displayName", ""),
                "homeScore": home.get("score"),
                "awayScore": away.get("score"),
            }
        day = end + timedelta(days=1)
    return list(events.values())


def resolve(name: str, by_norm: dict) -> str:
    n = norm(name)
    if n in by_norm:
        return by_norm[n]
    if n in ALIASES:
        return ALIASES[n]
    # tolérance : « Bodo/Glimt » vs « Bodø/Glimt », « Inter » vs « Inter Milan »
    for key, tid in by_norm.items():
        if key and (key in n or n in key):
            return tid
    return ALIASES.get(n, slugify(name))


def build(previous: dict) -> dict:
    standings = fetch_standings()

    # table de correspondance nom -> identifiant stable (issu du fichier existant)
    by_norm = {}
    meta = {}
    for t in previous.get("teams", []):
        by_norm[norm(t["name"])] = t["id"]
        by_norm[norm(t.get("code", "") or "")] = t["id"]
        meta[t["id"]] = t

    teams: dict[str, dict] = {}
    for row in standings:
        tid = resolve(row["name"], by_norm)
        prev = meta.get(tid, {})
        teams[tid] = {
            "id": tid,
            "code": prev.get("code") or (row["short"] or tid[:3].upper()),
            "name": prev.get("name") or row["name"],
            "short": prev.get("short") or row["short"] or tid[:3].upper(),
            "country": prev.get("country", ""),
            "espnId": row["espnId"],
            "pos": 0,
            "mp": row["mp"], "w": row["w"], "d": row["d"], "l": row["l"],
            "gf": row["gf"], "ga": row["ga"], "pts": row["pts"],
            "home": empty_line(),
            "away": empty_line(),
            "form": "",
            "results": [],
        }
    if len(teams) < 30:
        raise RuntimeError(f"seulement {len(teams)} équipes identifiées")

    # --- résultats + calendrier ---
    try:
        events = fetch_results()
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] résultats indisponibles : {exc}", file=sys.stderr)
        events = []

    played_pairs: set[tuple[str, str]] = set()  # (id domicile, id extérieur)
    total_played = 0
    for ev in sorted(events, key=lambda e: (e["date"], e["time"])):
        if ev["seasonType"] not in (14534, 1, None):
            continue  # on ne garde que la League Phase
        h = resolve(ev["home"], by_norm)
        a = resolve(ev["away"], by_norm)
        if h not in teams or a not in teams:
            continue
        if ev["state"] == "post" and ev["homeScore"] is not None and ev["awayScore"] is not None:
            hg, ag = int(ev["homeScore"]), int(ev["awayScore"])
            played_pairs.add((h, a))
            total_played += 1
            for tid, gf, ga, side in ((h, hg, ag, "home"), (a, ag, hg, "away")):
                t = teams[tid]
                d = t[side]
                d["mp"] += 1; d["gf"] += gf; d["ga"] += ga
                if gf > ga: d["w"] += 1; d["pts"] += 3; t["results"].append("W")
                elif gf == ga: d["d"] += 1; d["pts"] += 1; t["results"].append("D")
                else: d["l"] += 1; t["results"].append("L")

    # --- contrôle des splits : on exige une couverture complète des matchs joués ---
    matches_played = sum(t["mp"] for t in teams.values()) // 2
    splits_ok = (
        total_played >= matches_played
        and all(t["home"]["mp"] + t["away"]["mp"] == t["mp"] for t in teams.values())
        and all(t["home"]["gf"] + t["away"]["gf"] == t["gf"] for t in teams.values())
    )

    if not splits_ok:
        print("[WARN] splits incomplets : estimation à partir des totaux", file=sys.stderr)
    for t in teams.values():
        if not splits_ok:
            mp = t["mp"] or 1
            hp = round(mp / 2)
            ap = mp - hp
            t["home"] = {"mp": hp, "w": 0, "d": 0, "l": 0,
                         "gf": round(t["gf"] * hp / mp), "ga": round(t["ga"] * hp / mp), "pts": 0}
            t["away"] = {"mp": ap, "w": 0, "d": 0, "l": 0,
                         "gf": t["gf"] - t["home"]["gf"], "ga": t["ga"] - t["home"]["ga"], "pts": 0}
            t["splitsEstimated"] = True
        t["form"] = "".join(t.pop("results")[-5:])

    ordered = sorted(
        teams.values(),
        key=lambda t: (-t["pts"], -(t["gf"] - t["ga"]), -t["gf"], -t["away"]["gf"], -t["w"], t["name"]),
    )
    for i, t in enumerate(ordered, start=1):
        t["pos"] = i

    # --- calendrier : on part du calendrier publié et on retire les matchs joués ---
    def fixture_key(fx: dict) -> tuple[str, str]:
        """Clé d'une affiche : identifiants si présents, sinon noms normalisés."""
        h = fx.get("homeId") or resolve(fx.get("home", ""), by_norm)
        a = fx.get("awayId") or resolve(fx.get("away", ""), by_norm)
        return h, a

    fixtures = [f for f in previous.get("fixtures", []) if fixture_key(f) not in played_pairs]

    # ajout des affiches inédites renvoyées par ESPN
    known = {fixture_key(f) for f in fixtures}
    for ev in sorted(events, key=lambda e: (e["date"], e["time"])):
        if ev["state"] != "pre" or not ev["date"]:
            continue
        h = resolve(ev["home"], by_norm)
        a = resolve(ev["away"], by_norm)
        if h not in teams or a not in teams:
            continue
        key = (h, a)
        if key in played_pairs or key in known:
            continue
        known.add(key)
        fixtures.append({
            "date": ev["date"],
            "time": ev["time"],
            "round": f"J{max(t['mp'] for t in teams.values()) + 1}",
            "home": teams[h]["name"],
            "away": teams[a]["name"],
            "homeId": h,
            "awayId": a,
        })

    fixtures.sort(key=lambda f: (f.get("date") or "9999", f.get("time") or ""))

    matchday = max((t["mp"] for t in teams.values()), default=0)
    return {
        "season": "2026-27",
        "league": "UEFA Champions League",
        "slug": LEAGUE,
        "phase": "League Phase",
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matchday": matchday,
        "matchesPlayed": matches_played,
        "source": f"ESPN — League Phase J{matchday}",
        "splitsEstimated": not splits_ok,
        "teams": ordered,
        "fixtures": fixtures[:120],
    }


def sanity_check(data: dict) -> None:
    teams = data["teams"]
    if len(teams) < 30:
        raise RuntimeError(f"instantané invalide : {len(teams)} équipes")
    mps = {t["mp"] for t in teams}
    if len(mps) > 2:
        raise RuntimeError(f"matchs joués incohérents : {sorted(mps)}")
    total_gf = sum(t["gf"] for t in teams)
    total_ga = sum(t["ga"] for t in teams)
    if total_gf != total_ga:
        raise RuntimeError(f"ΣGF={total_gf} != ΣGA={total_ga}")
    goals = sum(1 for t in teams if t["mp"])
    if goals and not (1.2 < total_gf / (sum(t["mp"] for t in teams) / 2) < 6.0):
        raise RuntimeError("moyenne de buts aberrante")


def main() -> int:
    previous = read_previous()
    try:
        data = build(previous)
        sanity_check(data)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if previous.get("teams") == data["teams"] and previous.get("fixtures") == data["fixtures"]:
        print("[INFO] Aucun changement — fichier inchangé.")
        return 0

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[OK] {len(data['teams'])} équipes · J{data['matchday']} · "
        f"{data['matchesPlayed']} matchs joués · {len(data['fixtures'])} à venir"
        f"{' (splits estimés)' if data.get('splitsEstimated') else ''}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
