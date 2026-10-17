#!/usr/bin/env python3
"""Расчёт прогнозов с парсингом Flashscore и cybersport.ru."""

import os, httpx, re, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.eb_predictions.flashscore import fetch_all_results, find_match_result

MSK = ZoneInfo("Europe/Moscow")
wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])

def parse_datetime(dt_str):
    m = re.search(r"(\d{1,2})\.(\d{1,2})\s*(?:в\s*)?(\d{1,2}):(\d{2})", dt_str or "")
    if not m:
        return None
    try:
        day, month, hour, minute = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        now = datetime.now(MSK)
        return datetime(now.year, month, day, hour, minute, tzinfo=MSK)
    except Exception:
        return None

def is_finished(dt_str):
    match_dt = parse_datetime(dt_str)
    if not match_dt:
        return False
    return match_dt < datetime.now(MSK) - timedelta(hours=2)

def evaluate(bet, home, away, team1, team2):
    bet_l = (bet or "").lower()
    total = home + away
    if "тотал" in bet_l or "больше" in bet_l:
        if "2.5" in bet_l:
            return "won" if total > 2.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total > 3.5 else "lost"
        if "1.5" in bet_l:
            return "won" if total > 1.5 else "lost"
    if "меньше" in bet_l:
        if "2.5" in bet_l:
            return "won" if total < 2.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total < 3.5 else "lost"
    if "победа" in bet_l:
        if team1.lower() in bet_l:
            return "won" if home > away else "lost"
        if team2.lower() in bet_l:
            return "won" if away > home else "lost"
    return None

def main():
    with httpx.Client(timeout=60) as client:
        print("Загрузка результатов...")
        results = fetch_all_results(client, include_esports=True)
        print(f"Найдено результатов: {len(results)}")

        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 50, "status": "publish"},
            auth=auth,
        )
        posts = resp.json()

        settled = 0
        for post in posts:
            acf = post.get("acf") or {}
            status = (acf.get("prediction_status") or "").lower()
            if status in ("won", "lost"):
                continue

            dt = acf.get("match_datetime") or ""
            if not is_finished(dt):
                continue

            team1 = acf.get("pr_team1") or ""
            team2 = acf.get("pr_team2") or ""
            bet = acf.get("bet_type") or ""

            match = find_match_result(results, team1, team2)
            if not match:
                continue

            result = evaluate(bet, match["home_score"], match["away_score"], team1, team2)
            if not result:
                continue

            update = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                auth=auth,
                json={"acf": {"prediction_status": result, "final_score": match["score"]}},
            )
            if update.status_code == 200:
                settled += 1
                title = post.get("title", {}).get("rendered", "")[:40]
                print(f"Рассчитан: {title} → {result} ({match['score']}) [{match['source']}]")

        print(f"\nИтого рассчитано: {settled}")

if __name__ == "__main__":
    main()
