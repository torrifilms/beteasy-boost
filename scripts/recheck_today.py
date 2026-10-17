#!/usr/bin/env python3
"""Перепроверяет рассчитанные сегодня прогнозы по реальным результатам."""

import os, httpx, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

MSK = ZoneInfo("Europe/Moscow")
TSDB_KEY = "123"

def normalize(name: str) -> str:
    return (name or "").lower().replace("fc", "").replace(" ", "").strip()

def fetch_results(date: datetime) -> list[dict]:
    date_str = date.strftime("%Y-%m-%d")
    url = f"https://www.thesportsdb.com/api/v1/json/{TSDB_KEY}/eventsday.php?d={date_str}&s=Soccer"
    try:
        resp = client.get(url, timeout=30)
        data = resp.json()
        events = data.get("events") or []
        results = []
        for e in events:
            if e.get("strStatus") != "Match Finished":
                continue
            home = e.get("strHomeTeam") or ""
            away = e.get("strAwayTeam") or ""
            sh = e.get("intHomeScore")
            sa = e.get("intAwayScore")
            if sh is not None and sa is not None:
                results.append({
                    "home": home, "away": away,
                    "home_norm": normalize(home), "away_norm": normalize(away),
                    "score": f"{sh}-{sa}",
                    "home_score": int(sh), "away_score": int(sa),
                })
        print(f"Найдено завершённых матчей за {date_str}: {len(results)}")
        return results
    except Exception as exc:
        print(f"Ошибка API: {exc}")
        return []

def find_match(results: list, t1: str, t2: str):
    n1, n2 = normalize(t1), normalize(t2)
    for r in results:
        if (n1 in r["home_norm"] or r["home_norm"] in n1) and (n2 in r["away_norm"] or r["away_norm"] in n2):
            return r
        if (n2 in r["home_norm"] or r["home_norm"] in n2) and (n1 in r["away_norm"] or r["away_norm"] in n1):
            return r
    return None

def evaluate(bet: str, hs: int, aws: int, team1: str, team2: str) -> str | None:
    b = (bet or "").lower()
    total = hs + aws
    if "тотал" in b or "больше" in b:
        if "2.5" in b: return "won" if total > 2.5 else "lost"
        if "1.5" in b: return "won" if total > 1.5 else "lost"
        if "3.5" in b: return "won" if total > 3.5 else "lost"
    if "победа" in b:
        if team1.lower() in b: return "won" if hs > aws else "lost"
        if team2.lower() in b: return "won" if aws > hs else "lost"
    if "ничья" in b: return "won" if hs == aws else "lost"
    return None

print("Получаем прогнозы...")
resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 100, "status": "publish"})
posts = resp.json()

today = datetime.now(MSK).date()
results = fetch_results(datetime.now(MSK))

updated = 0
for p in posts:
    acf = p.get("acf") or {}
    status = (acf.get("prediction_status") or "").lower()
    if status not in ("won", "lost", "win", "lose"):
        continue

    dt_str = acf.get("match_datetime") or ""
    if "17.10" not in dt_str:
        continue

    team1 = acf.get("pr_team1") or ""
    team2 = acf.get("pr_team2") or ""
    bet = acf.get("bet_type") or ""

    match = find_match(results, team1, team2)
    if not match:
        print(f"Не найден: {team1} — {team2}")
        continue

    real_result = evaluate(bet, match["home_score"], match["away_score"], team1, team2)
    real_score = match["score"]

    if real_result and (real_result != status or acf.get("final_score") != real_score):
        r = client.post(
            f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
            json={"acf": {"prediction_status": real_result, "final_score": real_score}},
        )
        if r.status_code == 200:
            updated += 1
            print(f"Исправлен: {team1} — {team2} → {real_result} ({real_score})")

print(f"\nИсправлено: {updated}")
