"""Парсинг результатов CS2 с HLTV.org."""

from __future__ import annotations

import httpx
import re
from datetime import datetime


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def fetch_hltv_results(client: httpx.Client, days: int = 1) -> list[dict]:
    """Возвращает завершённые матчи CS2 с HLTV."""
    url = "https://www.hltv.org/results"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        resp = client.get(url, headers=headers, timeout=30, follow_redirects=True)
        html = resp.text

        results = []
        # Простой парсинг карточек результатов
        pattern = r'class="team-cell".*?>(.*?)</div>.*?class="team-cell".*?>(.*?)</div>.*?class="result-score".*?>(\d+)\s*-\s*(\d+)'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for home, away, sh, sa in matches[:30]:
            home = re.sub(r"<[^>]+>", "", home).strip()
            away = re.sub(r"<[^>]+>", "", away).strip()
            if home and away and sh.isdigit() and sa.isdigit():
                results.append({
                    "home": home,
                    "away": away,
                    "home_norm": _normalize(home),
                    "away_norm": _normalize(away),
                    "score": f"{sh}-{sa}",
                    "home_score": int(sh),
                    "away_score": int(sa),
                })
        return results
    except Exception as exc:
        print(f"HLTV ошибка: {exc}")
        return []


def find_hltv_result(results: list[dict], team1: str, team2: str) -> dict | None:
    n1, n2 = _normalize(team1), _normalize(team2)
    for r in results:
        if (n1 in r["home_norm"] or r["home_norm"] in n1) and (n2 in r["away_norm"] or r["away_norm"] in n2):
            return r
        if (n2 in r["home_norm"] or r["home_norm"] in n2) and (n1 in r["away_norm"] or r["away_norm"] in n1):
            return r
    return None
