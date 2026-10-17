#!/usr/bin/env python3
"""Рассчитывает прогнозы ЛИги чемпионов от 14.10 по реальным результатам."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

# Реальные результаты 14.10.2026
results = {
    "Шахтёр": ("3-1", "тотал больше 2.5", "win"),
    "Слован": ("0-3", "победа штутгарт", "win"),
    "Бетис": ("3-2", "тотал больше 2.5", "win"),
    "Манчестер Сити": ("2-4", "тотал меньше 3.5", "lose"),
    "Астон Вилла": ("6-0", "тотал больше 2.5", "win"),
    "Будё-Глимт": ("1-0", "тотал больше 3.5", "lose"),
    "Рома": ("3-4", "тотал меньше 3.5", "lose"),
    "ЛАСК": ("3-6", "победа ливерпуль", "win"),
    "Фейеноорд": ("3-2", "тотал меньше 3.5", "lose"),
}

resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 40, "status": "publish", "search": "14.10"})
posts = resp.json()

updated = 0
for p in posts:
    title = p.get("title", {}).get("rendered", "")
    acf = p.get("acf") or {}
    team1 = (acf.get("pr_team1") or "").lower()

    matched = None
    for key, data in results.items():
        if key.lower() in team1 or key.lower() in title.lower():
            matched = data
            break
    if not matched:
        continue

    score, expected_bet, status = matched
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"acf": {"prediction_status": "Выигран" if status == "win" else "Проигран", "final_score": score}},
    )
    print(f"{p['id']} {r.status_code} {team1[:30]} → {status} ({score})")
    if r.status_code == 200:
        updated += 1

print(f"\nОбновлено по реальным результатам: {updated}")
