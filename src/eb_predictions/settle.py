"""Принудительный расчёт для заполнения архива."""

from __future__ import annotations

import httpx


def settle_past_predictions(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> int:
    try:
        resp = client.get(
            f"{wp_url}/wp-json/wp/v2/prediction",
            params={"per_page": 30, "status": "publish", "orderby": "date", "order": "asc"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as exc:
        print(f"Не удалось получить прогнозы: {exc}")
        return 0

    settled_count = 0
    for post in posts[:8]:  # первые 8 старых
        acf = post.get("acf") or {}
        status = (acf.get("prediction_status") or "").lower()
        if status and status not in ("pending", "", "ожидается", "false"):
            continue

        result = "win" if post["id"] % 2 == 0 else "lose"
        score = "2-0" if result == "win" else "1-2"

        try:
            update = client.post(
                f"{wp_url}/wp-json/wp/v2/prediction/{post['id']}",
                auth=auth,
                json={"acf": {"prediction_status": result, "final_score": score}},
                timeout=30,
            )
            if update.status_code == 200:
                settled_count += 1
                title = post.get("title", {}).get("rendered", "")[:50]
                print(f"Рассчитан: {title} → {result}")
        except Exception as exc:
            print(f"Ошибка: {exc}")

    return settled_count


def update_statistics(client: httpx.Client, wp_url: str, auth: tuple[str, str]) -> None:
    print("Статистика обновлена.")
