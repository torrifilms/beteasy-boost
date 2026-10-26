#!/usr/bin/env python3
"""Расчёт прогнозов с реальными результатами:
- Футбол: API-Football (api-sports.io)
- Киберспорт (CS2, Dota 2): PandaScore
Ключи берутся из окружения: API_FOOTBALL_KEY, PANDASCORE_KEY
"""

import os, httpx, re, sys
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

# Fallback на случай, если API недоступны
try:
    from results_from_1710 import RESULTS_FROM_1710
except ImportError:
    RESULTS_FROM_1710 = []

MSK = ZoneInfo("Europe/Moscow")
wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
if not wp_url.startswith("http"):
    wp_url = "https://" + wp_url
auth = (os.environ.get("WP_USERNAME", ""), os.environ.get("WP_APP_PASSWORD", ""))

API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")
PANDASCORE_KEY = os.environ.get("PANDASCORE_KEY", "")

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

def evaluate(bet, home_score, away_score, team1, team2):
    bet_l = (bet or "").lower()
    total = home_score + away_score
    t1 = normalize(team1)
    t2 = normalize(team2)
    bet_n = normalize(bet)

    if "тотал" in bet_l or "больше" in bet_l:
        if "2.5" in bet_l or "25" in bet_n:
            return "won" if total > 2.5 else "lost"
        if "3.5" in bet_l or "35" in bet_n:
            return "won" if total > 3.5 else "lost"
        if "1.5" in bet_l or "15" in bet_n:
            return "won" if total > 1.5 else "lost"
    if "меньше" in bet_l:
        if "2.5" in bet_l or "25" in bet_n:
            return "won" if total < 2.5 else "lost"
        if "3.5" in bet_l or "35" in bet_n:
            return "won" if total < 3.5 else "lost"
    if "победа" in bet_l:
        if t1 and t1 in bet_n:
            return "won" if home_score > away_score else "lost"
        if t2 and t2 in bet_n:
            return "won" if away_score > home_score else "lost"
        if team1.lower() in bet_l:
            return "won" if home_score > away_score else "lost"
        if team2.lower() in bet_l:
            return "won" if away_score > home_score else "lost"
    return None

def find_match(results, team1, team2):
    n1, n2 = normalize(team1), normalize(team2)
    if not n1 or not n2:
        return None, False
    for r in results:
        h, a = normalize(r.get("home", "")), normalize(r.get("away", ""))
        if (n1 in h or h in n1) and (n2 in a or a in n2):
            return r, False
        if (n2 in h or h in n2) and (n1 in a or a in n1):
            return r, True
    return None, False

def fetch_api_football(client: httpx.Client, days: int = 7) -> list:
    """Футбол: результаты за последние N дней."""
    if not API_FOOTBALL_KEY:
        print("API_FOOTBALL_KEY не задан — пропускаем футбол")
        return []
    results = []
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    today = date.today()
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        try:
            resp = client.get(
                "https://v3.football.api-sports.io/fixtures",
                params={"date": d, "status": "FT"},
                headers=headers,
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"API-Football {d}: HTTP {resp.status_code} {resp.text[:200]}")
                continue
            data = resp.json()
            if data.get("errors"):
                print(f"API-Football {d}: errors {data['errors']}")
                continue
            for item in data.get("response", []):
                teams = item.get("teams", {})
                goals = item.get("goals", {})
                home = teams.get("home", {}).get("name", "")
                away = teams.get("away", {}).get("name", "")
                hs, as_ = goals.get("home"), goals.get("away")
                if home and away and hs is not None and as_ is not None:
                    results.append({
                        "home": home,
                        "away": away,
                        "score": f"{hs}-{as_}",
                        "home_score": int(hs),
                        "away_score": int(as_),
                        "source": "api-football",
                    })
        except Exception as e:
            print(f"API-Football {d}: {e}")
    print(f"API-Football: {len(results)} результатов")
    return results

def fetch_pandascore(client: httpx.Client, game: str, days: int = 7) -> list:
    """PandaScore: CS2 (csgo) или Dota 2."""
    if not PANDASCORE_KEY:
        print(f"PANDASCORE_KEY не задан — пропускаем {game}")
        return []
    results = []
    # CS2 использует префикс /csgo/ в PandaScore
    endpoint = f"https://api.pandascore.co/{game}/matches/past"
    try:
        resp = client.get(
            endpoint,
            params={"token": PANDASCORE_KEY, "per_page": 50, "sort": "-begin_at"},
            timeout=30,
        )
        matches = resp.json()
        cutoff = datetime.now(MSK) - timedelta(days=days)
        for m in matches:
            begin = m.get("begin_at") or ""
            if begin:
                try:
                    dt = datetime.fromisoformat(begin.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except Exception:
                    pass
            opponents = m.get("opponents") or []
            if len(opponents) < 2:
                continue
            home = opponents[0].get("opponent", {}).get("name", "")
            away = opponents[1].get("opponent", {}).get("name", "")
            results_data = m.get("results") or []
            if len(results_data) >= 2:
                hs = results_data[0].get("score", 0)
                as_ = results_data[1].get("score", 0)
                results.append({
                    "home": home,
                    "away": away,
                    "score": f"{hs}-{as_}",
                    "home_score": int(hs),
                    "away_score": int(as_),
                    "source": f"pandascore-{game}",
                })
    except Exception as e:
        print(f"PandaScore {game}: {e}")
    print(f"PandaScore {game}: {len(results)} результатов")
    return results

def main():
    print(f"WP URL: {wp_url}")
    results = []

    with httpx.Client(timeout=60) as client:
        results.extend(fetch_api_football(client, days=10))
        results.extend(fetch_pandascore(client, "csgo", days=10))   # CS2
        results.extend(fetch_pandascore(client, "dota2", days=10))

    # Fallback, если API ничего не вернули
    if not results:
        print("API не вернули результатов — используем локальный список")
        results = RESULTS_FROM_1710.copy()

    print(f"Всего результатов для сверки: {len(results)}")

    with httpx.Client(timeout=60) as client:
        try:
            resp = client.get(
                f"{wp_url}/wp-json/wp/v2/prediction",
                params={"per_page": 100, "status": "publish"},
                auth=auth,
            )
            posts = resp.json()
        except Exception as e:
            print(f"Ошибка подключения к WP: {e}")
            return

        settled = 0
        skipped = 0
        for post in posts:
            acf = post.get("acf") or {}
            status = (acf.get("prediction_status") or "").lower()
            if status in ("won", "lost"):
                skipped += 1
                continue

            dt = acf.get("match_datetime") or ""
            if not is_finished(dt):
                continue

            team1 = acf.get("pr_team1") or ""
            team2 = acf.get("pr_team2") or ""
            bet = acf.get("bet_type") or ""

            match, swapped = find_match(results, team1, team2)
            if not match:
                continue

            if swapped:
                h_score, a_score = match["away_score"], match["home_score"]
            else:
                h_score, a_score = match["home_score"], match["away_score"]

            result = evaluate(bet, h_score, a_score, team1, team2)
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
                    title = post.get("title", {}).get("rendered", "")[:50]
                    print(f"Рассчитан: {title} → {result} ({match['score']})")
            except Exception as e:
                print(f"Ошибка обновления: {e}")

        print(f"\nИтого рассчитано: {settled} | Уже было рассчитано: {skipped}")

if __name__ == "__main__":
    main()
