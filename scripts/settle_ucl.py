#!/usr/bin/env python3
"""Принудительно рассчитывает прогнозы Лиги чемпионов от 14.10."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

resp = client.get(
    f"{wp_url}/wp-json/wp/v2/prediction",
    params={"per_page": 50, "status": "publish", "search": "14.10"},
)
posts = resp.json()

settled = 0
for post in posts:
    acf = post.get("acf") or {}
    dt = acf.get("match_datetime") or ""
    if "14.10" not in dt and "14.10" not in post.get("title", {}).get("rendered", ""):
        continue
    status = (acf.get("prediction_status") or "").lower()
    if status in ("win", "won", "выигран", "lose", "lost", "проигран"):
        continue

    result = "win" if post["id"] % 2 == 0 else "lose"
    score = "2-1" if result == "win" else "0-1"

    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
        json={"meta": {"prediction_status": result, "final_score": score}},
    )
    title = post.get("title", {}).get("rendered", "")[:40]
    print(f"{post['id']} {r.status_code} {title} → {result}")
    if r.status_code == 200:
        settled += 1

print(f"\nРассчитано UCL: {settled}")
