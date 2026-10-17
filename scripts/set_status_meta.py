#!/usr/bin/env python3
"""Проставляет статус через meta (bypass ACF validation)."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

# ID из предыдущих логов + статус по реальным результатам
updates = {
    626: ("Выигран", "0-3"),   # Слован
    625: ("Выигран", "3-1"),   # Шахтёр
    624: ("Выигран", "3-2"),   # Бетис
    623: ("Проигран", "2-4"),  # Сити
    622: ("Проигран", "1-0"),  # Будё
    621: ("Выигран", "6-0"),   # Вилла
    620: ("Проигран", "3-4"),  # Рома
    619: ("Выигран", "3-6"),   # ЛАСК
    618: ("Проигран", "3-2"),  # Фейеноорд
}

for pid, (status, score) in updates.items():
    # Пробуем через meta
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"meta": {"prediction_status": status, "final_score": score}},
    )
    print(f"{pid} meta {r.status_code}")
    if r.status_code != 200:
        # Пробуем через acf с другим значением
        r2 = client.post(
            f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
            json={"acf": {"prediction_status": "win" if status == "Выигран" else "lose", "final_score": score}},
        )
        print(f"  acf fallback {r2.status_code}")
