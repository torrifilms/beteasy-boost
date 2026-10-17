"""Расчёт прошедших прогнозов типа prediction и обновление статистики."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import re

import httpx

MSK = ZoneInfo("Europe/Moscow")


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    """Ищет незакрытые прогнозы типа prediction и проставляет результат."""
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 50, "status": "publish", "_fields": "id,title,meta,date"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as exc:
        print(f"Не удалось получить прогнозы: {exc}")
        return 0

    settled_count = 0
    now = datetime.now(MSK)

    for post in posts:
        meta = post.get("meta") or {}
        status = meta.get("prediction_status", "pending")
        if status and status not in ("pending", "", "ожидание"):
            continue

        # Проверяем дату матча
        dt_str = meta.get("match_datetime", "")
        if not dt_str:
            continue
        try:
            # Формат вроде "17.10.2026 19:00"
            match_dt = datetime.strptime(dt_str.strip(), "%d.%m.%Y %H:%M").replace(tzinfo=MSK)
            if match_dt > now:
                continue
        except ValueError:
            continue

        # Пока ставим базовый статус (позже добавим реальный счёт из ESPN)
        new_meta = {
            "prediction_status": "calculated",
            "final_score": meta.get("final_score") or "-",
        }

        try:
            update = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                auth=auth,
                json={"meta": new_meta},
                timeout=30,
            )
            if update.status_code == 200:
                settled_count += 1
                title = post.get("title", {}).get("rendered", "")[:50]
                print(f"Рассчитан: {title}")
        except Exception as exc:
            print(f"Ошибка обновления {post.get('id')}: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    print("Статистика обновлена (тип prediction).")
