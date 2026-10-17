#!/usr/bin/env python3
"""Откатывает статусы у матчей, которые ещё не завершились."""

import os, httpx
from datetime import datetime
from zoneinfo import ZoneInfo

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

MSK = ZoneInfo("Europe/Moscow")
now = datetime.now(MSK)
print(f"Сейчас МСК: {now.strftime('%d.%m %H:%M')}")

resp = client.get(
    f"{wp_url}/wp-json/wp/v2/prediction",
    params={"per_page": 100, "status": "publish", "orderby": "date", "order": "desc"},
)
posts = resp.json()

reverted = 0
for p in posts:
    acf = p.get("acf") or {}
    dt_str = acf.get("match_datetime") or ""
    status = (acf.get("prediction_status") or "").lower()

    if status not in ("won", "lost", "win", "lose"):
        continue

    # Парсим дату матча
    match_time = None
    try:
        # Формат "17.10 в 17:00" или "17.10 17:00"
        import re
        m = re.search(r"(\d{1,2})\.(\d{1,2})\s*(?:в\s*)?(\d{1,2}):(\d{2})", dt_str)
        if m:
            day, month, hour, minute = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            match_time = datetime(now.year, month, day, hour, minute, tzinfo=MSK)
    except Exception:
        pass

    # Если матч ещё не начался или начался менее 2 часов назад — откатываем
    should_revert = False
    if match_time is None:
        should_revert = True
    elif match_time > now:
        should_revert = True
    elif (now - match_time).total_seconds() < 2 * 3600:
        should_revert = True

    if should_revert:
        r = client.post(
            f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
            json={"acf": {"prediction_status": "pending", "final_score": ""}},
        )
        if r.status_code == 200:
            reverted += 1
            title = p.get("title", {}).get("rendered", "")[:45]
            print(f"Откат: {title} ({dt_str})")

print(f"\nОткачено статусов: {reverted}")
