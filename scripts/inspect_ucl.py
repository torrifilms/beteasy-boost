#!/usr/bin/env python3
import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 30, "status": "publish", "search": "14.10"})
posts = resp.json()
print(f"Found {len(posts)} posts matching 14.10\n")

for p in posts[:15]:
    acf = p.get("acf") or {}
    title = p.get("title", {}).get("rendered", "")[:50]
    status = acf.get("prediction_status")
    dt = acf.get("match_datetime")
    print(f"ID {p['id']}: {title}")
    print(f"  status={status!r}  dt={dt!r}")
    print()
