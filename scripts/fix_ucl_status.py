#!/usr/bin/env python3
import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 40, "status": "publish", "search": "14.10"})
posts = resp.json()

updated = 0
for p in posts:
    acf = p.get("acf") or {}
    if acf.get("prediction_status") not in (None, "", "pending"):
        continue
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"acf": {"prediction_status": "Выигран", "final_score": "2-1"}},
    )
    title = p.get("title", {}).get("rendered", "")[:40]
    print(f"{p['id']} {r.status_code} {title}")
    if r.status_code == 200:
        updated += 1

print(f"\nОбновлено: {updated}")
