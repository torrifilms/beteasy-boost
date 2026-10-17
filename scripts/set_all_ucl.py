#!/usr/bin/env python3
"""Ставит won/lose через ACF (работающие значения)."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

updates = {
    626: ("won", "0-3"),    # Слован — победа Штутгарт
    625: ("won", "3-1"),    # Шахтёр — тотал > 2.5
    624: ("won", "3-2"),    # Бетис — тотал > 2.5
    623: ("lose", "2-4"),   # Сити — тотал < 3.5
    622: ("lose", "1-0"),   # Будё — тотал > 3.5
    621: ("won", "6-0"),    # Вилла — тотал > 2.5
    620: ("lose", "3-4"),   # Рома — тотал < 3.5
    619: ("won", "3-6"),    # ЛАСК — победа Ливерпуль
    618: ("lose", "3-2"),   # Фейеноорд — тотал < 3.5
}

for pid, (status, score) in updates.items():
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"acf": {"prediction_status": status, "final_score": score}},
    )
    print(f"{pid} {status} {r.status_code}")
