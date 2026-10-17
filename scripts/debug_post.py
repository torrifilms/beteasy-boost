#!/usr/bin/env python3
import os, sys, httpx

wp_url = os.environ.get("WP_BASE_URL", "https://beteasy.ru").rstrip("/")
auth = (os.environ["WP_USERNAME"], os.environ["WP_APP_PASSWORD"])
client = httpx.Client(timeout=30, auth=auth)

# Берём самый старый пост
resp = client.get(f"{wp_url}/wp-json/wp/v2/prediction", params={"per_page": 1, "orderby": "date", "order": "asc"})
post = resp.json()[0]
print("ID:", post["id"])
print("Title:", post["title"]["rendered"][:60])
print("ACF:", post.get("acf"))
print("Meta:", post.get("meta"))
