#!/usr/bin/env python3
import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=30, auth=auth)

pid = 623  # Сити — должен быть lose

for val in ["lose", "lost", "Проигран", "проигран", "no", "fail"]:
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"acf": {"prediction_status": val}},
    )
    print(f"'{val}': {r.status_code}")
    if r.status_code == 200:
        print("  OK")
        break
