"""Точка входа: расчёт прошедших прогнозов + публикация новых."""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from .matches import collect_picks
from .writer import write_posts, OpenAIText
from .settle import settle_past_predictions, update_statistics

MSK = ZoneInfo("Europe/Moscow")


def get_predictions_category_id(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int | None:
    """Ищет ID категории «Прогнозы» или похожей."""
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/categories",
            params={"per_page": 100, "search": "прогноз"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        for cat in resp.json():
            name = (cat.get("name") or "").lower()
            slug = (cat.get("slug") or "").lower()
            if any(k in name or k in slug for k in ("прогноз", "prognoz", "forecast", "tips")):
                print(f"Найдена категория: {cat.get('name')} (ID {cat.get('id')})")
                return cat.get("id")
    except Exception as exc:
        print(f"Не удалось получить категории: {exc}")
    return None


def main() -> None:
    wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")
    if not (wp_user and wp_pass):
        print("Нет WP_USERNAME / WP_APP_PASSWORD", file=sys.stderr)
        sys.exit(1)

    auth = (wp_user, wp_pass)
    client = httpx.Client(timeout=60, follow_redirects=True)

    print(f"[{datetime.now(MSK).isoformat()}] Начинаем расчёт прошедших матчей...")
    settled = settle_past_predictions(client, wp_url, auth)
    print(f"Рассчитано матчей: {settled}")

    print("Обновляем статистику...")
    update_statistics(client, wp_url, auth)

    print("Собираем новые прогнозы на сегодня/завтра...")
    limit = int(os.getenv("MAX_MATCHES", "12"))
    picks = collect_picks(client, limit)
    if not picks:
        print("Нет подходящих матчей для публикации.")
        return

    cat_id = get_predictions_category_id(client, wp_url, auth)

    llm_key = os.getenv("LLM_API_KEY")
    text_client = None
    if llm_key:
        text_client = OpenAIText(
            api_key=llm_key,
            base_url=os.getenv("LLM_BASE_URL", "https://api.x.ai/v1"),
            model=os.getenv("LLM_MODEL", "grok-4.7"),
            client=client,
        )

    texts = write_posts(picks, text_client)

    published = 0
    for pick in picks:
        html = texts.get(pick.match_key, "")
        if not html:
            continue
        # Добавляем структурированные данные для последующего расчёта
        meta_comment = (
            f"<!-- BETEASY_META {json.dumps({
                'match_key': pick.match_key,
                'team1': pick.team1,
                'team2': pick.team2,
                'bet': pick.bet_type,
                'odds': pick.odds,
                'kickoff': pick.kickoff.isoformat(),
                'sport': pick.sport,
                'league': pick.league,
            }, ensure_ascii=False)} -->"
        )
        full_html = meta_comment + html

        title = f"{pick.team1} — {pick.team2}: {pick.bet_type}"
        payload: dict = {
            "title": title,
            "content": full_html,
            "status": os.getenv("WP_POST_STATUS", "publish"),
        }
        if cat_id:
            payload["categories"] = [cat_id]

        try:
            resp = client.post(
                f"{wp_url}/wp-json/wp/v2/posts",
                auth=auth,
                json=payload,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                published += 1
                print(f"Опубликован: {title}")
            else:
                print(f"Ошибка публикации {title}: {resp.status_code} {resp.text[:300]}")
        except Exception as exc:
            print(f"Исключение при публикации: {exc}")

    print(f"Готово. Опубликовано новых прогнозов: {published}")


if __name__ == "__main__":
    main()
