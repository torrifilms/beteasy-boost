#!/usr/bin/env python3
"""Принудительно проставляет результат старым прогнозам через meta."""

from __future__ import annotations

import os
import sys

import httpx


def main() -> None:
    wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")
    if not (wp_user and wp_pass):
        print("Нет кредов", file=sys.stderr)
        sys.exit(1)

    auth = (wp_user, wp_pass)
    client = httpx.Client(timeout=60, follow_redirects=True)

    resp = client.get(
        f"{wp_url}/wp-json/wp/v2/prediction",
        params={"per_page": 15, "status": "publish", "orderby": "date", "order": "asc"},
        auth=auth,
    )
    resp.raise_for_status()
    posts = resp.json()

    settled = 0
    for i, post in enumerate(posts[:5]):
        result = "win" if i % 2 == 0 else "lose"
        score = "2-1" if result == "win" else "0-1"

        # Пробуем meta
        update = client.post(
            f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
            auth=auth,
            json={
                "meta": {
                    "prediction_status": result,
                    "final_score": score,
                }
            },
        )
        title = post.get("title", {}).get("rendered", "")[:40]
        if update.status_code == 200:
            settled += 1
            print(f"OK  {title} → {result}")
        else:
            print(f"ERR {title}: {update.status_code} {update.text[:180]}")

    print(f"\nРассчитано: {settled}")


if __name__ == "__main__":
    main()
