"""Русские названия команд. Ключ — нормализованное имя ESPN."""

from __future__ import annotations

import re

_RAW: dict[str, str] = {
    # Premier League
    "AFC Bournemouth": "Борнмут",
    "Bournemouth": "Борнмут",
    "Arsenal": "Арсенал",
    "Aston Villa": "Астон Вилла",
    "Brentford": "Брентфорд",
    "Brighton & Hove Albion": "Брайтон",
    "Brighton": "Брайтон",
    "Chelsea": "Челси",
    "Crystal Palace": "Кристал Пэлас",
    "Everton": "Эвертон",
    "Fulham": "Фулхэм",
    "Liverpool": "Ливерпуль",
    "Manchester City": "Манчестер Сити",
    "Manchester United": "Манчестер Юнайтед",
    "Newcastle United": "Ньюкасл",
    "Nottingham Forest": "Ноттингем Форест",
    "Tottenham Hotspur": "Тоттенхэм",
    "West Ham United": "Вест Хэм",
    "Wolverhampton Wanderers": "Вулверхэмптон",
    "Ipswich Town": "Ипсвич",
    "Hull City": "Халл Сити",

    # La Liga
    "Alavés": "Алавес",
    "Alaves": "Алавес",
    "Athletic Club": "Атлетик",
    "Athletic Bilbao": "Атлетик",
    "Atlético Madrid": "Атлетико",
    "Atletico Madrid": "Атлетико",
    "FC Barcelona": "Барселона",
    "Barcelona": "Барселона",
    "Real Betis": "Бетис",
    "Real Madrid": "Реал Мадрид",
    "Real Sociedad": "Реал Сосьедад",
    "Villarreal": "Вильярреал",
    "Elche": "Эльче",
    "Espanyol": "Эспаньол",
    "Sevilla": "Севилья",
    "Valencia": "Валенсия",
    "Getafe": "Хетафе",
    "Girona": "Жирона",
    "Las Palmas": "Лас-Пальмас",
    "Mallorca": "Мальорка",
    "Osasuna": "Осасуна",
    "Rayo Vallecano": "Райо Вальекано",
    "Celta Vigo": "Сельта",

    # Serie A
    "AC Milan": "Милан",
    "Milan": "Милан",
    "Inter": "Интер",
    "Internazionale": "Интер",
    "Juventus": "Ювентус",
    "Napoli": "Наполи",
    "Roma": "Рома",
    "Lazio": "Лацио",
    "Atalanta": "Аталанта",
    "Fiorentina": "Фиорентина",
    "Bologna": "Болонья",
    "Torino": "Торино",
    "Udinese": "Удинезе",
    "Venezia": "Венеция",
    "Monza": "Монца",
    "Como": "Комо",
    "Parma": "Парма",
    "Cagliari": "Кальяри",
    "Empoli": "Эмполи",
    "Lecce": "Лечче",
    "Genoa": "Дженоа",
    "Verona": "Верона",

    # Bundesliga
    "Bayern Munich": "Бавария",
    "FC Bayern Munich": "Бавария",
    "Borussia Dortmund": "Боруссия Д",
    "Bayer Leverkusen": "Байер",
    "RB Leipzig": "РБ Лейпциг",
    "Eintracht Frankfurt": "Айнтрахт",
    "VfB Stuttgart": "Штутгарт",
    "Borussia Mönchengladbach": "Боруссия М",
    "Wolfsburg": "Вольфсбург",
    "Werder Bremen": "Вердер",
    "Union Berlin": "Унион Берлин",
    "1. FC Union Berlin": "Унион Берлин",
    "Mainz": "Майнц",
    "Mainz 05": "Майнц",
    "Schalke 04": "Шальке",
    "Schalke": "Шальке",
    "FC Augsburg": "Аугсбург",
    "Augsburg": "Аугсбург",
    "SV Elversberg": "Эльверсберг",
    "Elversberg": "Эльверсберг",
    "SC Paderborn 07": "Падерборн",
    "Paderborn": "Падерборн",
    "Hoffenheim": "Хоффенхайм",
    "Freiburg": "Фрайбург",
    "Heidenheim": "Хайденхайм",
    "St. Pauli": "Санкт-Паули",

    # Ligue 1
    "Paris Saint-Germain": "ПСЖ",
    "PSG": "ПСЖ",
    "Marseille": "Марсель",
    "Lyon": "Лион",
    "Monaco": "Монако",
    "Lille": "Лилль",
    "Nice": "Ницца",
    "Rennes": "Ренн",
    "Lens": "Ланс",
    "Strasbourg": "Страсбур",
    "Toulouse": "Тулуза",
    "Nantes": "Нант",
    "Reims": "Реймс",
    "Montpellier": "Монпелье",
    "Brest": "Брест",
    "Le Havre": "Гавр",
    "Angers": "Анже",
    "Auxerre": "Осер",
    "Saint-Étienne": "Сент-Этьенн",
}


def _norm(name: str) -> str:
    text = name.casefold().replace("’", "'").replace(".", " ")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-zа-я0-9 ]+", " ", text)
    text = re.sub(r"\b(fc|afc|sc|ac|cf|osc|sv|vfb|vfl|rcd|cd|as|ogc|rc|fsv|tsg|1)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_INDEX = {_norm(english): russian for english, russian in _RAW.items()}


def russian_team_name(name: str) -> str:
    found = _INDEX.get(_norm(name))
    return found if found else name.strip()
