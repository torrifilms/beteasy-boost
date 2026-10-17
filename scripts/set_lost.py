#!/usr/bin/env python3
import os, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=30, auth=auth)

losers = {
    623: "2-4",  # Сити
    622: "1-0",  # Будё
    620: "3-4",  # Рома
    618: "3-2",  # Фейеноорд
}

for pid, score in losers.items():
    r = client.post(
        f"{wp_url}/wp-json/wp/v2/prediction/{pid}",
        json={"acf": {"prediction_status": "lost", "final_score": score}},
    )
    print(f"{pid} lost {r.status_code}")
