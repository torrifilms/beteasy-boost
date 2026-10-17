#!/usr/bin/env python3
"""Исправляет киберспортивные прогнозы."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

fixes = [
    ("Black Phoenix", "FORZE Reload", "2-0", "won"),  # Победа Black Phoenix — зашла
]

print("Ищем прогнозы...")
resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 50, "status": "publish"})
posts = resp.json()

for team1, team2, score, result in fixes:
    for p in posts:
        acf = p.get("acf") or {}
        t1 = (acf.get("pr_team1") or "").strip()
        t2 = (acf.get("pr_team2") or "").strip()

        if team1.lower() in t1.lower() and team2.lower() in t2.lower():
            r = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
                json={"acf": {"prediction_status": result, "final_score": score}},
            )
            if r.status_code == 200:
                print(f"Исправлен: {t1} — {t2} → {result} ({score})")
            else:
                print(f"Ошибка {p['id']}: {r.status_code}")
            break
    else:
        print(f"Не найден: {team1} — {team2}")
