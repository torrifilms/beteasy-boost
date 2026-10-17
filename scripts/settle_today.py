#!/usr/bin/env python3
"""Расчёт завершённых матчей 17.10.2026."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

# Реальные результаты
RESULTS = {
    ("манчестер сити", "ипсвич"): ("3-2", 3, 2),
    ("брентфорд", "ливерпуль"): ("1-2", 1, 2),
    ("фулхэм", "халл"): ("1-0", 1, 0),
    ("бетис", "барселона"): ("2-5", 2, 5),
}

def evaluate(bet, home, away, team1, team2):
    bet_l = (bet or "").lower()
    total = home + away
    if "тотал" in bet_l or "больше" in bet_l:
        if "2.5" in bet_l:
            return "won" if total > 2.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total > 3.5 else "lost"
    if "победа" in bet_l:
        if team1 in bet_l:
            return "won" if home > away else "lost"
        if team2 in bet_l:
            return "won" if away > home else "lost"
    return None

def find_result(team1, team2):
    t1, t2 = team1.lower(), team2.lower()
    for (a, b), data in RESULTS.items():
        if a in t1 and b in t2:
            return data
        if b in t1 and a in t2:
            return (data[0], data[2], data[1])
    return None

resp = client.get(
    f"{wp_url}/wp-json/wp/v2/prediction",
    params={"per_page": 50, "status": "publish", "orderby": "date", "order": "desc"},
)
posts = resp.json()

settled = 0
for p in posts:
    acf = p.get("acf") or {}
    dt = acf.get("match_datetime") or ""
    status = (acf.get("prediction_status") or "").lower()

    if "17.10" not in dt:
        continue
    if status in ("won", "lost", "win", "lose"):
        continue

    team1 = (acf.get("pr_team1") or "").lower()
    team2 = (acf.get("pr_team2") or "").lower()
    bet = acf.get("bet_type") or ""

    result_data = find_result(team1, team2)
    if not result_data:
        continue

    score, home, away = result_data
    result = evaluate(bet, home, away, team1, team2)
    if not result:
        continue

    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"acf": {"prediction_status": result, "final_score": score}},
    )
    if r.status_code == 200:
        settled += 1
        title = p.get("title", {}).get("rendered", "")[:40]
        print(f"Рассчитан: {title} → {result} ({score})")

print(f"\nИтого рассчитано: {settled}")
