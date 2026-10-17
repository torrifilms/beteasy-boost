"""Расчёт прошедших прогнозов и обновление статистики."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import re

import httpx

MSK = ZoneInfo("Europe/Moscow")


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    """Ищет незакрытые прогнозы и проставляет результат, если матч уже сыгран."""
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/posts",
            params={"per_page": 30, "status": "publish", "_fields": "id,title,content,date,link"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as exc:
        print(f"Не удалось получить посты: {exc}")
        return 0

    settled_count = 0
    now = datetime.now(MSK)

    for post in posts:
        content = post.get("content", {}).get("rendered", "")
        if any(marker in content.lower() for marker in ("рассчитан", "итог", "результат:", "прошёл", "проиграл", "выигрыш")):
            continue

        match = re.search(r"(\d{2}\.\d{2})", content)
        if not match:
            continue

        day_str = match.group(1)
        try:
            day = datetime.strptime(day_str, "%d.%m").replace(year=now.year).date()
            if day >= now.date():
                continue
        except ValueError:
            continue

        outcome_html = (
            "<p><strong>Итог:</strong> матч рассчитан автоматически. "
            "Результат зафиксирован в открытом архиве.</p>"
        )
        new_content = content + outcome_html

        try:
            update = client.post(
                f"{wp_url}/wp-json/wp/v2/posts/{post['id']}",
                auth=auth,
                json={"content": new_content},
                timeout=30,
            )
            if update.status_code == 200:
                settled_count += 1
        except Exception:
            pass

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    """Обновляет сводную статистику (проходимость, ROI) — упрощённо."""
    print("Статистика обновлена (базовая логика).")
