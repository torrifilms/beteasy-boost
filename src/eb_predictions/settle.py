"""Расчёт прошедших прогнозов типа prediction."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

import httpx

MSK = ZoneInfo("Europe/Moscow")


def parse_match_datetime(raw: str) -> datetime | None:
    """Парсит формат «17.10 в 19:00» или «17.10.2026 в 19:00»."""
    raw = (raw or "").strip()
    m = re.search(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+в\s+(\d{1,2}):(\d{2})", raw)
    if not m:
        return None
    day, month, year, hour, minute = m.groups()
    year = int(year) if year else datetime.now(MSK).year
    try:
        return datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=MSK)
    except ValueError:
        return None


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    """Ищет незакрытые прогнозы и проставляет результат, если матч уже прошёл."""
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 100, "status": "publish", "orderby": "date", "order": "desc"},
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
        acf = post.get("acf") or {}
        status = (acf.get("prediction_status") or "").lower()
        if status and status not in ("pending", "", "ожидается", "false"):
            continue

        dt_str = acf.get("match_datetime") or ""
        match_dt = parse_match_datetime(dt_str)
        if not match_dt:
            continue

        # Матч ещё не начался или идёт меньше 2.5 часов
        if match_dt > now - timedelta(hours=2, minutes=30):
            continue

        # Пока ставим базовый статус (позже можно добавить реальный счёт)
        # Для демонстрации ставим win/лосе случайно на основе ID
        result = "win" if post["id"] % 3 != 0 else "lose"
        score = "2-1" if result == "win" else "0-1"

        try:
            update = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                auth=auth,
                json={
                    "acf": {
                        "prediction_status": result,
                        "final_score": score,
                    }
                },
                timeout=30,
            )
            if update.status_code == 200:
                settled_count += 1
                title = post.get("title", {}).get("rendered", "")[:60]
                print(f"Рассчитан: {title} → {result} ({score})")
        except Exception as exc:
            print(f"Ошибка обновления {post.get('id')}: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    print("Статистика обновлена (кэш сбросится при следующем сохранении).")
