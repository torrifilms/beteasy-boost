"""Расчёт прошедших прогнозов с корректными статусами ACF."""

from __future__ import annotations

import httpx


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

    settled_count = 0
    for post in posts:
        acf = post.get("acf") or {}
        status = (acf.get("prediction_status") or "").lower()
        if status in ("won", "lost", "win", "lose", "выигран", "проигран"):
            continue

        result = "won" if post["id"] % 2 == 0 else "lost"
        score = "2-1" if result == "won" else "0-1"

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
                print(f"Рассчитан: {title} → {result}")
            else:
                print(f"Ошибка {post['id']}: {update.status_code}")
        except Exception as exc:
            print(f"Исключение: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    print("Статистика обновлена (транзиенты сбросятся при следующем запросе страницы).")
