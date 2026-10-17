"""Парсинг результатов с Flashscore и cybersport.ru."""

from __future__ import annotations

import httpx
import re
from datetime import datetime


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9а-яё]", "", (name or "").lower())


def fetch_flashscore_results(client: httpx.Client, sport: str = "football") -> list[dict]:
    """Парсит результаты с Flashscore."""
    urls = {
        "football": "https://www.flashscore.com/football/",
        "hockey": "https://www.flashscore.com/hockey/",
        "basketball": "https://www.flashscore.com/basketball/",
    }
    url = urls.get(sport, urls["football"])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    try:
        resp = client.get(url, headers=headers, timeout=30, follow_redirects=True)
        html = resp.text
        results = []

        # Парсинг карточек матчей
        pattern = r'data-event-id="[^"]+".*?class="event__participant[^"]*">([^<]+)</.*?class="event__participant[^"]*">([^<]+)</.*?class="event__score[^"]*">(\d+)</.*?class="event__score[^"]*">(\d+)</'
        matches = re.findall(pattern, html, re.DOTALL)

        for home, away, sh, sa in matches[:50]:
            home = home.strip()
            away = away.strip()
            if home and away and sh.isdigit() and sa.isdigit():
                results.append({
                    "home": home,
                    "away": away,
                    "home_norm": _normalize(home),
                    "away_norm": _normalize(away),
                    "score": f"{sh}-{sa}",
                    "home_score": int(sh),
                    "away_score": int(sa),
                    "source": "flashscore",
                })
        return results
    except Exception as exc:
        print(f"Flashscore ошибка: {exc}")
        return []


def fetch_cybersport_results(client: httpx.Client) -> list[dict]:
    """Парсит результаты киберспорта с cybersport.ru."""
    url = "https://www.cybersport.ru/matches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        resp = client.get(url, headers=headers, timeout=30, follow_redirects=True)
        html = resp.text
        results = []

        # Парсинг матчей киберспорта
        pattern = r'class="match-team[^"]*">([^<]+)</.*?class="match-team[^"]*">([^<]+)</.*?class="match-score[^"]*">(\d+)\s*[-:]​*\s*(\d+)'
        matches = re.findall(pattern, html, re.DOTALL)

        for home, away, sh, sa in matches[:30]:
            home = home.strip()
            away = away.strip()
            if home and away and sh.isdigit() and sa.isdigit():
                results.append({
                    "home": home,
                    "away": away,
                    "home_norm": _normalize(home),
                    "away_norm": _normalize(away),
                    "score": f"{sh}-{sa}",
                    "home_score": int(sh),
                    "away_score": int(sa),
                    "source": "cybersport",
                })
        return results
    except Exception as exc:
        print(f"Cybersport.ru ошибка: {exc}")
        return []


def find_match_result(results: list[dict], team1: str, team2: str) -> dict | None:
    """Ищет результат матча по названиям команд."""
    n1, n2 = _normalize(team1), _normalize(team2)
    if not n1 or not n2:
        return None

    for r in results:
        h, a = r["home_norm"], r["away_norm"]
        if (n1 in h or h in n1) and (n2 in a or a in n2):
            return r
        if (n2 in h or h in n2) and (n1 in a or a in n1):
            return r
    return None


def fetch_all_results(client: httpx.Client, include_esports: bool = True) -> list[dict]:
    """Собирает результаты со всех источников."""
    results = []
    results.extend(fetch_flashscore_results(client, "football"))
    results.extend(fetch_flashscore_results(client, "hockey"))
    if include_esports:
        results.extend(fetch_cybersport_results(client))
    return results
