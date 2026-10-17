#!/usr/bin/env python3
"""Публикует прогнозы на CS2 и Dota 2."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

predictions = [
    # CS2
    {
        "team1": "Aurora Gaming",
        "team2": "FURIA",
        "league": "Thunderpick World Championship 2026",
        "datetime": "17.10 в 17:00",
        "bet": "Победа Aurora Gaming",
        "odds": "1.85",
        "sport": "cs2",
        "risk": "Средний",
    },
    {
        "team1": "Heroic",
        "team2": "100 Thieves",
        "league": "Stake Pulse Beat III 2026",
        "datetime": "17.10 в 17:00",
        "bet": "Тотал карт больше 2.5",
        "odds": "1.72",
        "sport": "cs2",
        "risk": "Низкий",
    },
    {
        "team1": "Black Phoenix",
        "team2": "FORZE Reload",
        "league": "NODWIN Clutch Series Season 13",
        "datetime": "17.10 в 17:00",
        "bet": "Победа Black Phoenix",
        "odds": "1.90",
        "sport": "cs2",
        "risk": "Средний",
    },
    # Dota 2
    {
        "team1": "Yellow Submarine",
        "team2": "Team Spirit Academy",
        "league": "EPL Masters III Play-In",
        "datetime": "17.10 в 16:30",
        "bet": "Победа Yellow Submarine",
        "odds": "1.45",
        "sport": "dota2",
        "risk": "Низкий",
    },
    {
        "team1": "Dawn Bulls",
        "team2": "Yellow Submarine",
        "league": "EPL Masters III Play-In",
        "datetime": "17.10 в 19:00",
        "bet": "Тотал карт больше 2.5",
        "odds": "1.68",
        "sport": "dota2",
        "risk": "Средний",
    },
    {
        "team1": "Zero Tenacity",
        "team2": "Inner Circle",
        "league": "EPL Masters III Play-In",
        "datetime": "17.10 в 19:00",
        "bet": "Победа Zero Tenacity",
        "odds": "1.75",
        "sport": "dota2",
        "risk": "Средний",
    },
]

for p in predictions:
    title = f"{p['team1']} — {p['team2']}: прогноз"
    content = f"""<p>{p['league']}: {p['team1']} против {p['team2']}.</p>
<p>Прогноз: <strong>{p['bet']}</strong> за {p['odds']}.</p>
<p>Матч начнётся {p['datetime']} МСК. 18+.</p>"""

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "acf": {
            "pr_team1": p["team1"],
            "pr_team2": p["team2"],
            "league": p["league"],
            "match_datetime": p["datetime"],
            "bet_type": p["bet"],
            "odds": p["odds"],
            "stake": "50",
            "risk": p["risk"],
            "bank": "2",
            "prediction_status": "pending",
            "final_score": "",
            "pr_is_top": False,
            "sport": p["sport"],
        },
    }

    r = client.post(f"{wp_url}/wp-json/wp/v2/prediction", json=payload)
    print(f"{title}: {r.status_code}")
