"""Русские названия команд. Ключ — нормализованное имя ESPN."""

from __future__ import annotations

import re

_RAW: dict[str, str] = {
    "AFC Bournemouth": "Борнмут",
    "Bournemouth": "Борнмут",
    "Alavés": "Алавес",
    "Alaves": "Алавес",
    "Deportivo Alavés": "Алавес",
    "Arsenal": "Арсенал",
    "Aston Villa": "Астон Вилла",
    "Athletic Club": "Атлетик",
    "Athletic Bilbao": "Атлетик",
    "Atlético Madrid": "Атлетико",
    "Atletico Madrid": "Атлетико",
    "FC Barcelona": "Барселона",
    "Barcelona": "Барселона",
    "Bayer Leverkusen": "Байер",
    "Bayern Munich": "Бавария",
    "FC Bayern Munich": "Бавария",
    "Borussia Dortmund": "Боруссия Д",
    "Brentford": "Брентфорд",
    "Brighton & Hove Albion": "Брайтон",
    "Chelsea": "Челси",
    "Crystal Palace": "Кристал Пэлас",
    "Everton": "Эвертон",
    "Fulham": "Фулхэм",
    "Liverpool": "Ливерпуль",
    "Manchester City": "Манчестер Сити",
    "Manchester United": "Манчестер Юнайтед",
    "Newcastle United": "Ньюкасл",
    "Tottenham Hotspur": "Тоттенхэм",
    "Real Madrid": "Реал Мадрид",
    "Barcelona": "Барселона",
    "Juventus": "Ювентус",
    "Inter": "Интер",
    "AC Milan": "Милан",
    "Napoli": "Наполи",
    "PSG": "ПСЖ",
    "Paris Saint-Germain": "ПСЖ",
}


def _norm(name: str) -> str:
    text = name.casefold().replace("’", "'").replace(".", " ")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-zа-я0-9 ]+", " ", text)
    text = re.sub(r"\b(fc|afc|sc|ac|cf|osc|sv|vfb|vfl|rcd|cd|as|ogc|rc|fsv|tsg)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_INDEX = {_norm(english): russian for english, russian in _RAW.items()}


def russian_team_name(name: str) -> str:
    found = _INDEX.get(_norm(name))
    return found if found else name.strip()
