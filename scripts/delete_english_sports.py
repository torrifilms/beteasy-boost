#!/usr/bin/env python3
"""Удаляет прогнозы с английскими названиями только в обычных видах спорта (не киберспорт)."""

import os, httpx, re

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

def has_latin(s: str) -> bool:
    return bool(re.search(r"[A-Za-z]", s or ""))

def is_esports(sport: str, league: str, title: str) -> bool:
    text = f"{sport} {league} {title}".lower()
    return any(x in text for x in ("dota", "cs2", "cs:go", "valorant", "lol", "league of legends", "esport", "кибер"))

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 100, "status": "publish"})
posts = resp.json()

deleted = 0
for p in posts:
    acf = p.get("acf") or {}
    t1 = acf.get("pr_team1") or ""
    t2 = acf.get("pr_team2") or ""
    sport = acf.get("sport") or ""
    league = acf.get("league") or ""
    title = p.get("title", {}).get("rendered", "")

    if is_esports(sport, league, title):
        continue
    if has_latin(t1) or has_latin(t2):
        r = client.delete(f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}?force=true")
        print(f"Удалён {p['id']}: {title[:50]} ({r.status_code})")
        if r.status_code in (200, 201):
            deleted += 1

print(f"\nУдалено (не киберспорт): {deleted}")
