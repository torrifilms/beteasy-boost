"""Точка входа: расчёт + публикация в prediction с ACF (русские названия, без дублей, с перелинковкой)."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from .matches import collect_picks
from .writer import write_posts, OpenAIText
from .settle import settle_past_predictions, update_statistics
from .names import russian_team_name

MSK = ZoneInfo("Europe/Moscow")


def map_risk(raw: str) -> str:
    r = (raw or "").lower()
    if any(x in r for x in ("низк", "low", "никак")):
        return "Никакой"
    if any(x in r for x in ("высок", "high")):
        return "Высокий"
    return "Средний"


def map_sport(raw: str) -> str:
    r = (raw or "").lower()
    if "football" in r or "футбол" in r or "soccer" in r:
        return "футбол"
    if "hockey" in r or "хоккей" in r:
        return "хоккей"
    if "tennis" in r or "теннис" in r:
        return "теннис"
    if "basket" in r or "баскет" in r:
        return "баскетбол"
    return "футбол"


def format_match_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m в %H:%M")


def get_existing_keys_and_posts(client: httpx.Client, wp_url: str, auth: tuple) -> tuple[set[str], list[dict]]:
    keys = set()
    posts = []
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 100, "status": "publish", "orderby": "date", "order": "desc"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        for post in resp.json():
            acf = post.get("acf") or {}
            t1 = (acf.get("pr_team1") or "").strip()
            t2 = (acf.get("pr_team2") or "").strip()
            dt = (acf.get("match_datetime") or "").strip()
            if t1 and t2 and dt:
                keys.add(f"{t1}|{t2}|{dt}")
                keys.add(f"{t2}|{t1}|{dt}")
            title = post.get("title", {}).get("rendered", "")
            link = post.get("link", "")
            if title and link and not any(c.isascii() and c.isalpha() for c in title):
                posts.append({"title": title, "link": link})
    except Exception as exc:
        print(f"Не удалось получить существующие прогнозы: {exc}")
    return keys, posts


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

    print("Проверяем существующие прогнозы (защита от дублей + перелинковка)...")
    existing, other_posts = get_existing_keys_and_posts(client, wp_url, auth)
    print(f"Найдено существующих ключей: {len(existing)}, постов для ссылок: {len(other_posts)}")

    print("Собираем новые прогнозы на сегодня/завтра...")
    limit = int(os.getenv("MAX_MATCHES", "12"))
    picks = collect_picks(client, limit)
    if not picks:
        print("Нет подходящих матчей для публикации.")
        return

    llm_key = os.getenv("LLM_API_KEY")
    text_client = None
    if llm_key:
        text_client = OpenAIText(
            api_key=llm_key,
            base_url=os.getenv("LLM_BASE_URL", "https://api.x.ai/v1"),
            model=os.getenv("LLM_MODEL", "grok-4.7"),
            client=client,
        )

    texts = write_posts(picks, text_client, other_posts)

    published = 0
    skipped = 0
    for pick in picks:
        html = texts.get(pick.match_key, "")
        if not html:
            continue

        team1_ru = russian_team_name(pick.team1)
        team2_ru = russian_team_name(pick.team2)

        kickoff_str = ""
        if hasattr(pick, "kickoff"):
            kickoff_str = format_match_datetime(pick.kickoff)

        key = f"{team1_ru}|{team2_ru}|{kickoff_str}"
        if key in existing:
            skipped += 1
            print(f"Пропуск (дубль): {team1_ru} — {team2_ru} ({kickoff_str})")
            continue

        acf_fields = {
            "pr_team1": team1_ru,
            "pr_team2": team2_ru,
            "league": pick.league or "",
            "match_datetime": kickoff_str,
            "bet_type": pick.bet_type,
            "odds": str(pick.odds),
            "stake": "50",
            "risk": map_risk(getattr(pick, "risk", "средний")),
            "bank": str(getattr(pick, "bank", 2)),
            "prediction_status": "pending",
            "final_score": "",
            "pr_is_top": False,
            "sport": map_sport(getattr(pick, "sport", "football")),
        }

        title = f"{team1_ru} — {team2_ru}: прогноз"
        payload = {
            "title": title,
            "content": html,
            "status": os.getenv("WP_POST_STATUS", "publish"),
            "acf": acf_fields,
        }

        try:
            resp = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction",
                auth=auth,
                json=payload,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                published += 1
                existing.add(key)
                print(f"Опубликован: {title} ({kickoff_str})")
            else:
                print(f"Ошибка публикации {title}: {resp.status_code} {resp.text[:400]}")
        except Exception as exc:
            print(f"Исключение при публикации: {exc}")

    print(f"Готово. Опубликовано новых: {published}, пропущено дублей: {skipped}")


if __name__ == "__main__":
    main()
