#!/usr/bin/env python3
"""Проставляет prediction_status=win свежим рассчитанным прогнозам через ACF."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=30, auth=auth)

# ID из предыдущей проверки точности
ids = [595, 594, 593, 592, 591, 590, 589]

for pid in ids:
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"acf": {"prediction_status": "win"}},
    )
    print(pid, r.status_code, r.text[:120] if r.status_code != 200 else "OK")
