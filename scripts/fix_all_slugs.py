#!/usr/bin/env python3
"""Исправляет слаги всех постов и прогнозов на английский транслит."""

import os
import re
import httpx

WP_URL = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
AUTH = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
    "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
    "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}

def transliterate(text: str) -> str:
    if not text:
        return ""
    result = []
    for char in text.lower():
        result.append(TRANSLIT.get(char, char))
    slug = "".join(result)
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "item"

def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[а-яё]", s, re.I))

def fix_type(client: httpx.Client, post_type: str):
    print(f"\n=== {post_type} ===")
    page = 1
    fixed = 0
    while True:
        resp = client.get(
            f"{WP_URL}/wp-json/wp/v2/{post_type}",
            params={"per_page": 100, "page": page, "status": "publish,draft,pending"},
            auth=AUTH,
        )
        if resp.status_code != 200:
            break
        items = resp.json()
        if not items:
            break
        for item in items:
            slug = item.get("slug", "")
            title = item.get("title", {}).get("rendered", "")
            if has_cyrillic(slug) or not slug:
                new_slug = transliterate(title)
                if new_slug and new_slug != slug:
                    r = client.post(
                        f"{WP_URL}/wp-json/wp/v2/{post_type}/{item['id']}",
                        json={"slug": new_slug},
                        auth=AUTH,
                    )
                    status = "OK" if r.status_code in (200, 201) else f"ERR {r.status_code}"
                    print(f"  {item['id']}: {slug[:40]} → {new_slug[:40]} [{status}]")
                    fixed += 1
        if len(items) < 100:
            break
        page += 1
    print(f"Исправлено {post_type}: {fixed}")
    return fixed

def main():
    with httpx.Client(timeout=60) as client:
        total = 0
        for pt in ("posts", "prediction", "pages"):
            total += fix_type(client, pt)
        print(f"\nВсего исправлено: {total}")

if __name__ == "__main__":
    main()
