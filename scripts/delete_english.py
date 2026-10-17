#!/usr/bin/env python3
"""Удаляет прогнозы, у которых команды на английском."""

import os, httpx, re

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

def has_latin(s: str) -> bool:
    return bool(re.search(r"[A-Za-z]", s or ""))

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 100, "status": "publish"})
posts = resp.json()

deleted = 0
for p in posts:
    acf = p.get("acf") or {}
    t1 = acf.get("pr_team1") or ""
    t2 = acf.get("pr_team2") or ""
    title = p.get("title", {}).get("rendered", "")
    if has_latin(t1) or has_latin(t2) or has_latin(title):
        r = client.delete(f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}?force=true")
        print(f"Удалён {p['id']}: {title[:50]} ({r.status_code})")
        if r.status_code in (200, 201):
            deleted += 1

print(f"\nУдалено: {deleted}")
