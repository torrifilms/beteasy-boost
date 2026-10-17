"""Точка входа с отладкой полей."""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

MSK = ZoneInfo("Europe/Moscow")


def main() -> None:
    wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")
    if not (wp_user and wp_pass):
        print("Нет кредов", file=sys.stderr)
        sys.exit(1)

    auth = (wp_user, wp_pass)
    client = httpx.Client(timeout=60, follow_redirects=True)

    print("=== ОТЛАДКА ПОЛЕЙ ПРОГНОЗОВ ===")
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 3, "orderby": "date", "order": "desc", "_fields": "id,title,date,acf,meta"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
        for p in posts:
            print(f"\n--- ID {p.get('id')} | {p.get('title', {}).get('rendered', '')} ---")
            print("ACF:", json.dumps(p.get("acf"), ensure_ascii=False, indent=2) if p.get("acf") else "нет")
            print("META:", json.dumps(p.get("meta"), ensure_ascii=False, indent=2) if p.get("meta") else "нет")
    except Exception as exc:
        print(f"Ошибка: {exc}")
        if hasattr(exc, 'response'):
            print(exc.response.text[:500])


if __name__ == "__main__":
    main()
