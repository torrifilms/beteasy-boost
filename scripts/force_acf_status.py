#!/usr/bin/env python3
"""Пробует разные способы записи статуса в ACF."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

pid = 625  # Шахтёр — тестовый

# Сначала посмотрим текущие данные
r = client.get(f"{wp_url}/wp-json/wp/v2/prediction/{pid}?_fields=acf,meta")
print("Current:", r.json().get("acf", {}).get("prediction_status"))

# Пробуем разные варианты значений
for val in ["Выигран", "win", "won", "выигран"]:
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"acf": {"prediction_status": val, "final_score": "3-1"}},
    )
    print(f"ACF '{val}': {r.status_code}")
    if r.status_code == 200:
        print("  Success!")
        break
