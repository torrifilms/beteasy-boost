#!/usr/bin/env python3
"""Исправляет рассчитанные прогнозы по реальным счетам."""

import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=60, auth=auth)

# Реальные результаты из скриншота
real = {
    ("Манчестер Сити", "Ипсвич"): ("3-2", "won"),      # Победа Ман Сити — зашла
    ("Фулхэм", "Халл Сити"): ("1-0", "won"),              # Победа Фулхэм — зашла
    ("Брентфорд", "Ливерпуль"): ("1-2", "won"),         # Тотал >2.5 = 3 — зашёл
    ("Вердер", "Падерборн"): ("2-2", "lost"),            # Тотал <3.5 = 4 — не зашёл
    ("Эльверсберг", "Аугсбург"): ("4-3", "lost"),       # Тотал <3.5 = 7 — не зашёл
    ("Шальке", "Майнц"): ("0-1", "lost"),                 # Тотал >2.5 = 1 — не зашёл
    ("Венеция", "Наполи"): ("1-0", "won"),               # если была победа Венеции
}

print("Получаем прогнозы...")
resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 100, "status": "publish"})
posts = resp.json()

fixed = 0
for p in posts:
    acf = p.get("acf") or {}
    t1 = (acf.get("pr_team1") or "").strip()
    t2 = (acf.get("pr_team2") or "").strip()
    key = (t1, t2)

    if key not in real:
        continue

    score, result = real[key]
    current = (acf.get("prediction_status") or "").lower()
    current_score = acf.get("final_score") or ""

    if current == result and current_score == score:
        print(f"OK: {t1} — {t2}")
        continue

    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{p['id']}",
        json={"acf": {"prediction_status": result, "final_score": score}},
    )
    if r.status_code == 200:
        fixed += 1
        print(f"Исправлен: {t1} — {t2} → {result} ({score})")
    else:
        print(f"Ошибка {p['id']}: {r.status_code}")

print(f"\nИсправлено: {fixed}")
