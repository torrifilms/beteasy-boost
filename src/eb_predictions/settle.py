"""Расчёт прошедших прогнозов по реальным результатам."""

from __future__ import annotations

import httpx
import random
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .results import fetch_results, find_result

MSK = ZoneInfo("Europe/Moscow")


def _get_related_links(client: httpx.Client, wp_url: str, auth: tuple, exclude_id: int, limit: int = 3) -> str:
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 20, "status": "publish", "orderby": "date", "order": "desc"},
            auth=auth,
            timeout=20,
        )
        posts = [p for p in resp.json() if p["id"] != exclude_id]
        if not posts:
            return ""
        sample = random.sample(posts, min(limit, len(posts)))
        items = []
        for p in sample:
            title = p.get("title", {}).get("rendered", "")
            link = p.get("link", "")
            if title and link:
                items.append(f'<li><a href="{link}">{title}</a></li>')
        if items:
            return "<h3>Смотрите также</h3><ul>" + "".join(items) + "</ul>"
    except Exception:
        pass
    return ""


def _get_featured_image(client: httpx.Client, wp_url: str, auth: tuple, post_id: int) -> int | None:
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction/{post_id}",
            auth=auth,
            timeout=15,
        )
        media_id = resp.json().get("featured_media")
        return media_id if media_id else None
    except Exception:
        return None


def _parse_match_datetime(dt_str: str) -> datetime | None:
    m = re.search(r"(\d{1,2})\.(\d{1,2})\s*(?:в\s*)?(\d{1,2}):(\d{2})", dt_str or "")
    if not m:
        return None
    try:
        day, month, hour, minute = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        now = datetime.now(MSK)
        return datetime(now.year, month, day, hour, minute, tzinfo=MSK)
    except Exception:
        return None


def _evaluate_bet(bet: str, home_score: int, away_score: int, team1: str, team2: str) -> str | None:
    bet_l = (bet or "").lower()
    total = home_score + away_score

    if "тотал" in bet_l or "больше" in bet_l or "over" in bet_l:
        if "2.5" in bet_l:
            return "won" if total > 2.5 else "lost"
        if "1.5" in bet_l:
            return "won" if total > 1.5 else "lost"
        if "3.5" in bet_l:
            return "won" if total > 3.5 else "lost"

    if "победа" in bet_l:
        if team1.lower() in bet_l:
            return "won" if home_score > away_score else "lost"
        if team2.lower() in bet_l:
            return "won" if away_score > home_score else "lost"

    if "ничья" in bet_l or "дро" in bet_l:
        return "won" if home_score == away_score else "lost"

    return None


def _create_news(client: httpx.Client, wp_url: str, auth: tuple, prediction: dict, result: str, score: str) -> None:
    acf = prediction.get("acf") or {}
    team1 = acf.get("pr_team1") or "Команда 1"
    team2 = acf.get("pr_team2") or "Команда 2"
    league = acf.get("league") or ""
    bet = acf.get("bet_type") or "прогноз"
    odds = acf.get("odds") or ""
    pred_link = prediction.get("link", "")
    pred_id = prediction.get("id")

    status_ru = "зашёл" if result == "won" else "не зашёл"
    title = f"{team1} — {team2}: итоги прогноза ({score})"

    content = f"""<p>Матч <strong>{team1} — {team2}</strong>"""
    if league:
        content += f" ({league})"
    content += f" завершился. Итоговый счёт — <strong>{score}</strong>.</p>"

    content += "<h2>Результат прогноза</h2>"
    content += f"<p>Наш прогноз: <strong>{bet}</strong>"
    if odds:
        content += f" (коэффициент {odds})"
    content += ".</p>"
    content += f"<p>Статус: <strong>{status_ru.upper()}</strong>.</p>"

    if result == "won":
        content += "<p>Прогноз сыграл. Подробный разбор и логика выбора ставки доступны в оригинальном материале.</p>"
    else:
        content += "<p>Прогноз не сыграл. Разбор матча и причины выбора можно посмотреть в полной версии прогноза.</p>"

    if pred_link:
        content += f'<p><a href="{pred_link}"><strong>Открыть полный прогноз на {team1} — {team2}</strong></a></p>'

    related = _get_related_links(client, wp_url, auth, pred_id or 0)
    if related:
        content += related

    content += "<hr><p><small>18+. Прогнозы носят информационный характер и не являются гарантией выигрыша.</small></p>"

    featured = _get_featured_image(client, wp_url, auth, pred_id) if pred_id else None

    payload = {"title": title, "content": content, "status": "publish"}
    if featured:
        payload["featured_media"] = featured

    try:
        r = client.post(f"{wp_url}/wp-json/wp/v2/posts", auth=auth, json=payload, timeout=30)
        if r.status_code in (200, 201):
            print(f"  Новость: {title}")
    except Exception as exc:
        print(f"  Ошибка новости: {exc}")


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 50, "status": "publish", "orderby": "date", "order": "desc"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as exc:
        print(f"Не удалось получить прогнозы: {exc}")
        return 0

    now = datetime.now(MSK)
    results_cache: dict[str, list] = {}
    settled_count = 0

    for post in posts:
        acf = post.get("acf") or {}
        status = (acf.get("prediction_status") or "").lower()
        if status in ("won", "lost", "win", "lose", "выигран", "проигран"):
            continue

        team1 = acf.get("pr_team1") or ""
        team2 = acf.get("pr_team2") or ""
        bet = acf.get("bet_type") or ""
        dt_str = acf.get("match_datetime") or ""

        match_dt = _parse_match_datetime(dt_str)
        if not match_dt or match_dt > now - timedelta(hours=2):
            continue

        date_key = match_dt.strftime("%Y-%m-%d")
        if date_key not in results_cache:
            results_cache[date_key] = fetch_results(client, match_dt)

        match_result = find_result(results_cache[date_key], team1, team2)
        if not match_result:
            continue

        score = match_result["score"]
        result = _evaluate_bet(bet, match_result["home_score"], match_result["away_score"], team1, team2)
        if not result:
            continue

        try:
            update = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                auth=auth,
                json={"acf": {"prediction_status": result, "final_score": score}},
                timeout=30,
            )
            if update.status_code == 200:
                settled_count += 1
                title = post.get("title", {}).get("rendered", "")[:40]
                print(f"Рассчитан: {title} → {result} ({score})")
                _create_news(client, wp_url, auth, post, result, score)
        except Exception as exc:
            print(f"Исключение: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    print("Статистика обновлена (транзиенты сбросятся при следующем запросе страницы).")
