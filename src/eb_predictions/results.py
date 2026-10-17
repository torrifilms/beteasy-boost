"""Реальные результаты матчей через TheSportsDB."""

from __future__ import annotations

import httpx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")
TSDB_KEY = "123"


def _normalize(name: str) -> str:
    return (name or "").lower().replace("fc", "").replace(" ", "").strip()


def fetch_results(client: httpx.Client, date: datetime) -> list[dict]:
    """Возвращает список завершённых матчей за указанную дату."""
    date_str = date.strftime("%Y-%m-%d")
    url = f"https://www.thesportsdb.com/api/v1/json/{TSDB_KEY}/eventsday.php?d={date_str}&s=Soccer"
    try:
        resp = client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events") or []
        results = []
        for e in events:
            if e.get("strStatus") != "Match Finished":
                continue
            home = e.get("strHomeTeam") or ""
            away = e.get("strAwayTeam") or ""
            score_h = e.get("intHomeScore")
            score_a = e.get("intAwayScore")
            if score_h is not None and score_a is not None:
                results.append({
                    "home": home,
                    "away": away,
                    "home_norm": _normalize(home),
                    "away_norm": _normalize(away),
                    "score": f"{score_h}-{score_a}",
                    "home_score": int(score_h),
                    "away_score": int(score_a),
                })
        return results
    except Exception as exc:
        print(f"Ошибка получения результатов: {exc}")
        return []


def find_result(results: list[dict], team1: str, team2: str) -> dict | None:
    t1 = _normalize(team1)
    t2 = _normalize(team2)
    for r in results:
        if (t1 in r["home_norm"] or r["home_norm"] in t1) and (t2 in r["away_norm"] or r["away_norm"] in t2):
            return r
        if (t2 in r["home_norm"] or r["home_norm"] in t2) and (t1 in r["away_norm"] or r["away_norm"] in t1):
            return r
    return None
