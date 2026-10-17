#!/usr/bin/env python3
"""Добавляет блок «Смотрите также» ко всем прогнозам."""

import os, httpx, random

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 100, "status": "publish"})
posts = resp.json()

# Собираем пул для ссылок
pool = []
for p in posts:
    title = p.get("title", {}).get("rendered", "")
    link = p.get("link", "")
    if title and link:
        pool.append({"id": p["id"], "title": title, "link": link})

updated = 0
for p in posts:
    content = p.get("content", {}).get("rendered", "")
    if "Смотрите также" in content:
        continue

    others = [x for x in pool if x["id"] != p["id"]]
    if len(others) < 2:
        continue

    sample = random.sample(others, min(3, len(others)))
    links = ", ".join(f'<a href="{x["link"]}">{x["title"]}</a>' for x in sample)
    block = f'<p><strong>Смотрите также:</strong> {links}.</p>'

    new_content = content + block
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"content": new_content},
    )
    if r.status_code == 200:
        updated += 1
        print(f"Обновлён {p['id']}")

print(f"\nДобавлены ссылки в {updated} прогнозов")
