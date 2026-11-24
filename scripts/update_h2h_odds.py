#!/usr/bin/env python3
"""
Collecte les cotes 1X2 + le face-à-face (H2H) via l'API FootyStats
(https://footystats.org/api — api.football-data-api.com) pour les prochains
matchs de Premier League, et écrit data/h2h-odds.json.

Règles du registre « H2H Scanner » (calculées côté app, avec réglages) :
  R1. taux H2H ≥ 50 %  ET  (p_book − taux H2H) ≥ 10 pts  -> victoire sèche
  R2. favori à l'extérieur avec 50 % < p_book < 60 %     -> Over 1.5

Endpoints utilisés :
  /league-list?key=                    -> découverte league_id / season_id
  /league-matches?...&status=incomplete -> matchs à venir (+ ids)
  /match?match_id=                      -> odds_ft_1/x/2, odds_ft_over15, h2h

Sans FOOTYSTATS_API_KEY, le script sort proprement (code 0) sans rien écrire :
l'app reste utilisable en mode manuel.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "h2h-odds.json"

API = os.environ.get("FOOTYSTATS_API_BASE", "https://api.football-data-api.com")
UA = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36")

MAX_MATCHES = int(os.environ.get("H2H_MAX_MATCHES", "24"))
SLEEP = float(os.environ.get("H2H_SLEEP", "0.6"))
LEAGUE_HINTS = ("premier league", "champions league")


def slug(name: str) -> str:
    s = unicodedata.normalize("NFD", (name or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def fetch(path: str, key: str, **params) -> dict:
    params["key"] = key
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"{path}: {exc}") from exc
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path}: réponse non JSON ({body[:120]})") from exc
    if isinstance(data, dict) and data.get("success") is False:
        raise RuntimeError(f"{path}: API a renvoyé success=false ({str(data)[:160]})")
    return data


def as_list(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in ("data", "results", "leagues", "matches"):
            v = payload.get(k)
            if isinstance(v, list):
                return v
    return []


def discover_league(key: str) -> tuple[int, int, str]:
    """Trouve league_id + season_id de la Premier League (saison en cours)."""
    env_l, env_s = os.environ.get("FOOTYSTATS_LEAGUE_ID"), os.environ.get("FOOTYSTATS_SEASON_ID")
    if env_l and env_s:
        return int(env_l), int(env_s), "env"

    leagues = as_list(fetch("league-list", key))
    best = None
    for lg in leagues:
        name = str(lg.get("name") or "")
        country = str(lg.get("country") or "")
        low = name.lower()
        if "premier league" not in low or "women" in low or "u21" in low or "u19" in low:
            continue
        if country and "england" not in country.lower():
            continue
        seasons = lg.get("season") or lg.get("seasons") or []
        if isinstance(seasons, dict):
            seasons = [seasons]
        seasons = [s for s in seasons if isinstance(s, dict)]
        seasons.sort(key=lambda s: str(s.get("year") or s.get("name") or ""), reverse=True)
        if not seasons:
            continue
        s0 = seasons[0]
        sid = s0.get("id") or s0.get("season_id")
        if not sid:
            continue
        best = (int(lg.get("id")), int(sid), f"{name} {s0.get('year') or s0.get('name') or ''}")
        break
    if not best:
        raise RuntimeError("Premier League introuvable dans /league-list (utilise FOOTYSTATS_LEAGUE_ID / FOOTYSTATS_SEASON_ID)")
    return best


def upcoming_matches(key: str, league_id: int, season_id: int) -> list:
    payload = fetch("league-matches", key, league_id=league_id, season_id=season_id,
                    status="incomplete")
    now = time.time()
    rows = []
    for m in as_list(payload):
        if not isinstance(m, dict):
            continue
        kick = m.get("date_unix") or 0
        try:
            kick = int(float(kick))
        except (TypeError, ValueError):
            kick = 0
        if kick and kick < now - 3600:
            continue
        if str(m.get("status") or "").lower() in ("complete", "suspended", "canceled"):
            continue
        rows.append({
            "id": m.get("id"),
            "kickoff": kick,
            "home": m.get("home_name") or m.get("homeName") or "",
            "away": m.get("away_name") or m.get("awayName") or "",
            "homeId": m.get("homeID"),
            "awayId": m.get("awayID"),
            # certaines réponses de listes contiennent déjà les cotes
            "odds_home": m.get("odds_ft_1"),
            "odds_draw": m.get("odds_ft_x"),
            "odds_away": m.get("odds_ft_2"),
            "odds_over15": m.get("odds_ft_over15"),
        })
    rows.sort(key=lambda r: r["kickoff"] or 0)
    return rows[:MAX_MATCHES]


def to_float(value):
    try:
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def extract_match(key: str, row: dict) -> dict | None:
    """Complète une ligne avec les cotes et le H2H via /match."""
    # Le détail est indispensable : c'est lui qui porte le bloc H2H.
    detail = {}
    try:
        payload = fetch("match", key, match_id=row["id"])
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list):
            data = data[0] if data else {}
        detail = data or {}
    except Exception as exc:  # noqa: BLE001
        if not (row["odds_home"] and row["odds_away"]):
            raise
        print(f"[WARN] détail indisponible pour {row['id']} : {exc}", file=sys.stderr)
    time.sleep(SLEEP)

    odds_home = to_float(detail.get("odds_ft_1")) or to_float(row["odds_home"])
    odds_draw = to_float(detail.get("odds_ft_x")) or to_float(row["odds_draw"])
    odds_away = to_float(detail.get("odds_ft_2")) or to_float(row["odds_away"])
    over15 = to_float(detail.get("odds_ft_over15")) or to_float(row["odds_over15"])

    h2h_raw = detail.get("h2h") or {}
    pm = h2h_raw.get("previous_matches_results") or {}
    betting = h2h_raw.get("betting_stats") or {}

    def num(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0

    home_wins = num(pm.get("team_a_wins"))
    away_wins = num(pm.get("team_b_wins"))
    draws = num(pm.get("draw"))
    total = num(pm.get("totalMatches")) or (home_wins + away_wins + draws)

    if not total:
        h2h = None
    else:
        h2h = {
            "total": total,
            "homeWins": home_wins,
            "awayWins": away_wins,
            "draws": draws,
            "homeWinPct": round(100.0 * home_wins / total, 1),
            "awayWinPct": round(100.0 * away_wins / total, 1),
            "over15Pct": betting.get("over15Percentage"),
            "avgGoals": betting.get("avg_goals"),
        }

    if not (odds_home and odds_draw and odds_away):
        return None

    kick = row["kickoff"]
    dt = datetime.fromtimestamp(kick, tz=timezone.utc) if kick else None

    return {
        "id": row["id"],
        "date": dt.strftime("%Y-%m-%d") if dt else "",
        "time": dt.strftime("%H:%M") if dt else "",
        "home": row["home"],
        "away": row["away"],
        "homeId": slug(row["home"]),
        "awayId": slug(row["away"]),
        "odds": {
            "home": odds_home,
            "draw": odds_draw,
            "away": odds_away,
            "over15": over15,
        },
        "h2h": h2h,
    }


def main() -> int:
    key = (os.environ.get("FOOTYSTATS_API_KEY") or "").strip()
    if not key:
        print("[SKIP] FOOTYSTATS_API_KEY absent — aucune cote publiée (mode manuel dans l'app).")
        return 0
    if key.lower() in ("example", "demo", "test"):
        print("[SKIP] Clé de démonstration FootyStats : pas de cotes 2026-27.")
        return 0

    try:
        league_id, season_id, label = discover_league(key)
        print(f"[INFO] Ligue {league_id} / saison {season_id} ({label})")
        rows = upcoming_matches(key, league_id, season_id)
        print(f"[INFO] {len(rows)} match(s) à venir")

        matches = []
        for row in rows:
            try:
                m = extract_match(key, row)
                if m:
                    matches.append(m)
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] match {row.get('id')} ignoré : {exc}", file=sys.stderr)
            time.sleep(SLEEP)

        if not matches:
            print("[WARN] Aucun match avec cotes complètes — fichier inchangé.", file=sys.stderr)
            return 0

        prev = {}
        if OUT.exists():
            try:
                prev = json.loads(OUT.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                prev = {}

        payload = {
            "league": "Premier League",
            "season": "2026-27",
            "source": "FootyStats API (cotes 1X2 + H2H)",
            "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "leagueId": league_id,
            "seasonId": season_id,
            "matches": matches,
        }
        if prev.get("matches") == matches:
            print("[INFO] Cotes inchangées — fichier non réécrit.")
            return 0

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] {len(matches)} matchs écrits dans {OUT}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
