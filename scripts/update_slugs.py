#!/usr/bin/env python3
"""Обновляет слаги страниц турниров на английские."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

# Русское название -> английский слаг
slugs = {
    "Ла Лига": "la-liga",
    "Серия A": "serie-a",
    "Бундеслига": "bundesliga",
    "Лига 1": "ligue-1",
    "РПЛ": "rpl",
    "CS2": "cs2",
    "Dota 2": "dota-2",
    "Лига Европы": "europa-league",
    "Лига чемпионов": "champions-league",
    "АПЛ": "premier-league",
}

resp = client.get(f"{wp_url}/wp-json/wp/v2/pages", params={"per_page": 50, "status": "publish"})
pages = resp.json()

for page in pages:
    title = page.get("title", {}).get("rendered", "")
    for ru, en in slugs.items():
        if ru.lower() in title.lower():
            r = client.post(
                f"{wp_url}/wp-json/wp/v2/pages/{page['id']}",
                json={"slug": en},
            )
            print(f"{title} → /{en}/ ({r.status_code})")
            break
