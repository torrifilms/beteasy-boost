#!/usr/bin/env python3
"""Создаёт страницы турниров."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

tournaments = [
    ("Ла Лига", "Ла Лига"),
    ("Серия A", "Серия A"),
    ("Бундеслига", "Бундеслига"),
    ("Лига 1", "Лига 1"),
    ("РПЛ", "РПЛ"),
    ("CS2", "CS2"),
    ("Dota 2", "Dota 2"),
    ("Лига Европы", "Лига Европы"),
]

for title, league in tournaments:
    # Проверяем, существует ли уже
    check = client.get(f"{wp_url}/wp-json/wp/v2/pages", params={"search": title, "per_page": 5})
    exists = any(title.lower() in p.get("title", {}).get("rendered", "").lower() for p in check.json())
    if exists:
        print(f"Уже есть: {title}")
        continue

    payload = {
        "title": title,
        "status": "publish",
        "template": "page-tournament.php",
        "acf": {"league_filter": league},
        "content": f"<p>Прогнозы на матчи {title}.</p>",
    }
    r = client.post(f"{wp_url}/wp-json/wp/v2/pages", json=payload)
    print(f"{title}: {r.status_code}")
