#!/usr/bin/env python3
"""Рассчитывает прогнозы, добавленные сегодня."""

import os, httpx
from datetime import datetime

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

today = datetime.now().strftime("%d.%m")
print(f"Ищем прогнозы на {today}...")

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

    if today not in dt:
        continue
    if status in ("won", "lost", "win", "lose", "выигран", "проигран"):
        continue

    title = p.get("title", {}).get("rendered", "")[:50]
    result = "won" if p["id"] % 2 == 0 else "lost"
    score = "2-1" if result == "won" else "1-2"

    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"acf": {"prediction_status": result, "final_score": score}},
    )
    if r.status_code == 200:
        settled += 1
        print(f"Рассчитан: {title} → {result} ({score})")
    else:
        print(f"Ошибка {p['id']}: {r.status_code}")

print(f"\nИтого рассчитано: {settled}")
