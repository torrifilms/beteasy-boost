#!/usr/bin/env python3
"""Проверяет точность прогнозов."""

from __future__ import annotations

import os
import sys
from collections import defaultdict

import httpx

WIN = {"win", "won", "зашёл", "зашел", "выигран"}
LOSE = {"lose", "lost", "не зашёл", "не зашел", "проигран"}


def main() -> None:
    wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
    auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
    client = httpx.Client(timeout=60, auth=auth)

    resp = client.get(
        f"{wp_url}/wp-json/wp/v2/prediction",
        params={"per_page": 100, "status": "publish", "orderby": "date", "order": "desc"},
    )
    posts = resp.json()

    wins = loses = pending = 0
    roi = 0.0
    by_sport = defaultdict(lambda: {"win": 0, "lose": 0, "roi": 0.0})

    print(f"\nВсего прогнозов: {len(posts)}\n")
    print(f"{'ID':<6} {'Статус':<8} {'Коэф':<6} {'Счёт':<10} Заголовок")
    print("-" * 80)

    for post in posts:
        acf = post.get("acf") or {}
        status = (acf.get("prediction_status") or "").lower().strip()
        odds = float(acf.get("odds") or 0)
        score = str(acf.get("final_score") or "")
        sport = (acf.get("sport") or "other").lower()
        title = post.get("title", {}).get("rendered", "")[:42]

        if status in WIN:
            wins += 1
            roi += (odds - 1) if odds > 0 else 0
            by_sport[sport]["win"] += 1
            by_sport[sport]["roi"] += (odds - 1) if odds > 0 else 0
            mark = "WIN"
        elif status in LOSE:
            loses += 1
            roi -= 1
            by_sport[sport]["lose"] += 1
            by_sport[sport]["roi"] -= 1
            mark = "LOSE"
        else:
            pending += 1
            continue

        print(f"{post['id']:<6} {mark:<8} {odds:<6.2f} {score:<10} {title}")

    settled = wins + loses
    print("\n" + "=" * 40)
    print(f"Зашло: {wins}")
    print(f"Не зашло: {loses}")
    print(f"Ожидает: {pending}")
    if settled:
        print(f"Проходимость: {wins / settled * 100:.1f}%")
        print(f"ROI (флэт): {roi / settled * 100:+.1f}%")
    print("\nПо видам спорта:")
    for sport, d in sorted(by_sport.items(), key=lambda x: -(x[1]["win"] + x[1]["lose"])):
        s = d["win"] + d["lose"]
        if s:
            wr = d["win"] / s * 100
            r = d["roi"] / s * 100
            print(f"  {sport}: {d['win']}/{s} ({wr:.0f}%)  ROI {r:+.1f}%")


if __name__ == "__main__":
    main()
