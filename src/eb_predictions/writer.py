"""Текст прогноза с внутренними перелинковками на другие прогнозы."""

from __future__ import annotations

import json
import random
import sys
from typing import Protocol

import httpx

from .matches import PlannedPick

DISCLAIMER = (
    "<p><strong>Это мнение модели, не гарантия выигрыша.</strong> "
    "Самый вероятный исход посчитан по открытой линии на момент запуска. "
    "У легального букмекера в России коэффициент может быть другим. 18+.</p>"
)


class TextClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class OpenAIText:
    def __init__(self, api_key: str, base_url: str, model: str, client: httpx.Client) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = client

    def complete(self, prompt: str) -> str:
        body: dict = {
            "model": self.model,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты редактор спортивных прогнозов. Пишешь по-русски, коротко и по делу. "
                        "Не меняешь уже выбранную ставку и коэффициент. Не обещаешь выигрыш."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        if "api.x.ai" in self.base_url:
            body["reasoning_effort"] = "low"
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["choices"][0]["message"]["content"])


def _internal_links(other_posts: list[dict]) -> str:
    if not other_posts:
        return ""
    sample = random.sample(other_posts, min(3, len(other_posts)))
    links = []
    for p in sample:
        title = p.get("title", "")
        url = p.get("link", "")
        if title and url:
            links.append(f'<a href="{url}">{title}</a>')
    if not links:
        return ""
    return "<p><strong>Смотрите также:</strong> " + ", ".join(links) + ".</p>"


def fallback_html(pick: PlannedPick, other_posts: list[dict] | None = None) -> str:
    percent = round(pick.probability * 100)
    links = _internal_links(other_posts or [])
    return (
        f"<p>{pick.league}: {pick.team1} против {pick.team2}, начало {pick.match_datetime} МСК.</p>"
        f"<p>Самый вероятный исход по линии — <strong>{pick.bet_type}</strong> "
        f"за {pick.odds:.2f}. После снятия маржи у этого варианта около {percent}%.</p>"
        f"<p>Шанс первой команды на победу в паре команд — {pick.stake}%. "
        f"Доля банка для такой уверенности — {pick.bank}%.</p>"
        f"{links}"
        f"{DISCLAIMER}"
    )


def _prompt(picks: list[PlannedPick], other_posts: list[dict] | None) -> str:
    rows = [
        {
            "match_key": pick.match_key,
            "league": pick.league,
            "teams": f"{pick.team1} — {pick.team2}",
            "start_msk": pick.match_datetime,
            "bet": pick.bet_type,
            "odds": pick.odds,
            "probability_percent": round(pick.probability * 100),
            "team1_win_percent": pick.stake,
        }
        for pick in picks
    ]
    links_hint = ""
    if other_posts:
        sample = random.sample(other_posts, min(3, len(other_posts)))
        links_hint = " В конце добавь абзац <p><strong>Смотрите также:</strong> " + ", ".join(
            f'<a href="{p["link"]}">{p["title"]}</a>' for p in sample if p.get("link")
        ) + ".</p>"
    return (
        "Для каждого матча напиши разбор на 3–5 абзацев в HTML (только теги p, strong, ul, li, a). "
        "Ставку, коэффициент и процент не меняй. " + links_hint +
        " Верни JSON {\"items\":[{\"match_key\":\"...\",\"html\":\"...\"}]}.\n"
        + json.dumps(rows, ensure_ascii=False)
    )


def _loads(raw: str) -> object:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def write_posts(picks: list[PlannedPick], client: TextClient | None, other_posts: list[dict] | None = None) -> dict[str, str]:
    texts = {pick.match_key: fallback_html(pick, other_posts) for pick in picks}
    if client is None or not picks:
        return texts
    try:
        raw = client.complete(_prompt(picks, other_posts))
        parsed = _loads(raw)
        items = parsed.get("items") if isinstance(parsed, dict) else None
        if not isinstance(items, list):
            return texts
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("match_key") or "")
            html = str(item.get("html") or "").strip()
            if key in texts and html:
                texts[key] = html + DISCLAIMER
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Текст модели не получен, оставлен короткий разбор: {exc}", file=sys.stderr)
        return texts
    return texts
