#!/usr/bin/env python3
"""Проверяет точность прогнозов по данным с сайта."""

from __future__ import annotations

import os
import sys
from collections import defaultdict

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
        params={"per_page": 100, "status": "publish", "orderby": "date", "order": "desc"},
        auth=auth,
    )
    resp.raise_for_status()
    posts = resp.json()

    wins = loses = pending = 0
    roi = 0.0
    by_sport = defaultdict(lambda: {"win": 0, "lose": 0, "roi": 0.0})

    print(f"\nВсего прогнозов: {len(posts)}\n")
    print(f"{'ID':<6} {'Статус':<8} {'Коэф':<6} {'Счёт':<8} Заголовок")
    print("-" * 80)

    for post in posts:
        acf = post.get("acf") or {}
        meta = post.get("meta") or {}
        status = (acf.get("prediction_status") or meta.get("prediction_status") or "").lower()
        odds = float(acf.get("odds") or meta.get("odds") or 0)
        score = acf.get("final_score") or meta.get("final_score") or ""
        sport = (acf.get("sport") or meta.get("sport") or "other").lower()
        title = post.get("title", {}).get("rendered", "")[:45]

        if status in ("win", "зашёл", "зашел"):
            wins += 1
            roi += (odds - 1) if odds > 0 else 0
            by_sport[sport]["win"] += 1
            by_sport[sport]["roi"] += (odds - 1) if odds > 0 else 0
            mark = "WIN"
        elif status in ("lose", "не зашёл", "не зашел"):
            loses += 1
            roi -= 1
            by_sport[sport]["lose"] += 1
            by_sport[sport]["roi"] -= 1
            mark = "LOSE"
        else:
            pending += 1
            mark = "-—"

        if mark != "-—":
            print(f"{post['id']:<6} {mark:<8} {odds:<6.2f} {score:<8} {title}")

    settled = wins + loses
    print("\n" + "=" * 40)
    print(f"Зашло: {wins}")
    print(f"Не зашло: {loses}")
    print(f"Ожидает: {pending}")
    if settled:
        print(f"Проходимость: {wins / settled * 100:.1f}%")
        print(f"ROI (флэт): {roi / settled * 100:.1f}%")
    print("\nПо видам спорта:")
    for sport, d in sorted(by_sport.items(), key=lambda x: -(x[1]["win"] + x[1]["lose"])):
        s = d["win"] + d["lose"]
        if s:
            wr = d["win"] / s * 100
            r = d["roi"] / s * 100
            print(f"  {sport}: {d['win']}/{s} ({wr:.0f}%)  ROI {r:+.1f}%")


if __name__ == "__main__":
    main()
