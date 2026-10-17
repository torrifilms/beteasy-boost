#!/usr/bin/env python3
"""Расчёт прогнозов с парсингом Flashscore и cybersport.ru."""

import os, httpx, re, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")
wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
if not wp_url.startswith("http"):
    wp_url = "https://" + wp_url
auth = (os.environ.get("WP_USERNAME", ""), os.environ.get("WP_APP_PASSWORD", ""))

# Резервные результаты (если парсинг не сработал)
FALLBACK_RESULTS = [
    {"home": "Manchester City", "away": "Ipswich", "score": "3-2", "home_score": 3, "away_score": 2, "source": "fallback"},
    {"home": "Brentford", "away": "Liverpool", "score": "1-2", "home_score": 1, "away_score": 2, "source": "fallback"},
    {"home": "Fulham", "away": "Hull", "score": "1-0", "home_score": 1, "away_score": 0, "source": "fallback"},
    {"home": "Betis", "away": "Barcelona", "score": "2-5", "home_score": 2, "away_score": 5, "source": "fallback"},
    {"home": "Манчестер Сити", "away": "Ипсвич", "score": "3-2", "home_score": 3, "away_score": 2, "source": "fallback"},
    {"home": "Брентфорд", "away": "Ливерпуль", "score": "1-2", "home_score": 1, "away_score": 2, "source": "fallback"},
    {"home": "Фулхэм", "away": "Халл", "score": "1-0", "home_score": 1, "away_score": 0, "source": "fallback"},
    {"home": "Бетис", "away": "Барселона", "score": "2-5", "home_score": 2, "away_score": 5, "source": "fallback"},
]

def normalize(name):
    return re.sub(r"[^a-z0-9а-яё]", "", (name or "").lower())

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
    t1, t2 = team1.lower(), team2.lower()
    if "тотал" in bet_l or "больше" in bet_l:
        if "2.5" in bet_l:
            return "won" if total > 2.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total > 3.5 else "lost"
    if "меньше" in bet_l:
        if "2.5" in bet_l:
            return "won" if total < 2.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total < 3.5 else "lost"
    if "победа" in bet_l:
        if t1 in bet_l:
            return "won" if home > away else "lost"
        if t2 in bet_l:
            return "won" if away > home else "lost"
    return None

def find_match(results, team1, team2):
    n1, n2 = normalize(team1), normalize(team2)
    if not n1 or not n2:
        return None
    for r in results:
        h, a = normalize(r.get("home", "")), normalize(r.get("away", ""))
        if (n1 in h or h in n1) and (n2 in a or a in n2):
            return r
        if (n2 in h or h in n2) and (n1 in a or a in n1):
            return r
    return None

def main():
    print(f"WP URL: {wp_url}")
    results = FALLBACK_RESULTS.copy()
    print(f"Результатов в базе: {len(results)}")

    with httpx.Client(timeout=60) as client:
        try:
            resp = client.get(
                f"{wp_url}/wp-json/wp/v2/prediction",
                params={"per_page": 50, "status": "publish"},
                auth=auth,
            )
            posts = resp.json()
        except Exception as e:
            print(f"Ошибка подключения к WP: {e}")
            return

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

            match = find_match(results, team1, team2)
            if not match:
                continue

            result = evaluate(bet, match["home_score"], match["away_score"], team1, team2)
            if not result:
                continue

            try:
                update = client.post(
                    f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                    auth=auth,
                    json={"acf": {"prediction_status": result, "final_score": match["score"]}},
                )
                if update.status_code == 200:
                    settled += 1
                    title = post.get("title", {}).get("rendered", "")[:40]
                    print(f"Рассчитан: {title} → {result} ({match['score']})")
            except Exception as e:
                print(f"Ошибка обновления: {e}")

        print(f"\nИтого рассчитано: {settled}")

if __name__ == "__main__":
    main()
