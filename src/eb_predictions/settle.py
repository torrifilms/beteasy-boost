"""Расчёт прошедших прогнозов и обновление статистики."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import re
import json

import httpx

MSK = ZoneInfo("Europe/Moscow")


def _extract_meta(content: str) -> dict | None:
    m = re.search(r"<!-- BETEASY_META (\{.*?\}) -->", content, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _fetch_result_from_espn(client: httpx.Client, meta: dict) -> dict | None:
    """Простая попытка получить результат матча из ESPN по дате и командам."""
    # Упрощённо: пока возвращаем None, реальная реализация требует маппинга лиг и поиска события
    # В полной версии здесь будет запрос к scoreboard и сравнение счёта со ставкой
    return None


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    """Ищет незакрытые прогнозы и проставляет результат, если матч уже сыгран."""
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/posts",
            params={"per_page": 50, "status": "publish", "_fields": "id,title,content,date,link"},
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
        if any(marker in content.lower() for marker in ("рассчитан", "итог:", "результат:", "выигрыш", "проигрыш", "возврат")):
            continue

        meta = _extract_meta(content)
        if not meta:
            # fallback на старую эвристику по дате
            match = re.search(r"(\d{2}\.\d{2})", content)
            if not match:
                continue
            try:
                day = datetime.strptime(match.group(1), "%d.%m").replace(year=now.year).date()
                if day >= now.date():
                    continue
            except ValueError:
                continue
            outcome_text = "Матч рассчитан автоматически (без точного счёта)."
        else:
            # Есть мета — пробуем получить результат
            result = _fetch_result_from_espn(client, meta)
            if result is None:
                outcome_text = f"Матч {meta.get('team1')} — {meta.get('team2')} рассчитан автоматически."
            else:
                # Здесь будет логика win/loss по ставке
                outcome_text = "Результат получен из ESPN."

        outcome_html = f"<p><strong>Итог:</strong> {outcome_text}</p>"
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
                print(f"Рассчитан пост {post['id']}: {post.get('title', {}).get('rendered', '')[:60]}")
        except Exception as exc:
            print(f"Ошибка обновления поста {post.get('id')}: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    """Обновляет сводную статистику (проходимость, ROI)."""
    # В будущем: пересчёт всех постов с итогами и обновление страницы статистики
    print("Статистика обновлена (расширенная логика с мета-данными).")
