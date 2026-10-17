"""Отладка заполненных полей."""
from __future__ import annotations
import os, sys, json
import httpx

def main():
    wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
    auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
    client = httpx.Client(timeout=60, auth=auth, follow_redirects=True)
    print("=== ПРОВЕРКА ACF ПОЛЕЙ ===")
    r = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 2, "orderby": "date", "order": "desc"})
    for p in r.json():
        print(f"\nID {p['id']}: {p['title']['rendered']}")
        acf = p.get("acf") or {}
        print(json.dumps({k: acf.get(k) for k in ["pr_team1","pr_team2","match_datetime","bet_type","odds","sport","prediction_status","risk"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
