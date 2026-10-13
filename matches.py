"""Матчи на сегодня и завтра по Москве из открытой линии ESPN."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from eb_predictions.names import russian_team_name
from eb_predictions.odds import Outcome, most_likely, outcomes_from_espn, risk_and_bank, team1_percent

MSK = ZoneInfo("Europe/Moscow")

LEAGUES: tuple[tuple[str, str, str, str], ...] = (
    ("football", "soccer", "eng.1", "АПЛ"),
    ("football", "soccer", "esp.1", "Ла Лига"),
    ("football", "soccer", "ger.1", "Бундеслига"),
    ("football", "soccer", "ita.1", "Серия A"),
    ("football", "soccer", "fra.1", "Лига 1"),
    ("football", "soccer", "uefa.champions", "Лига чемпионов"),
    ("football", "soccer", "uefa.europa", "Лига Европы"),
    ("football", "soccer", "rus.1", "РПЛ"),
    ("hockey", "hockey", "nhl", "НХЛ"),
    ("basketball", "basketball", "nba", "НБА"),
    ("tennis", "tennis", "atp", "ATP"),
)


@dataclass(frozen=True)
class PlannedPick:
    match_key: str
    sport: str
    league: str
    team1: str
    team2: str
    home_logo: str
    away_logo: str
    kickoff: datetime
    match_datetime: str
    bet_type: str
    odds: float
    stake: int
    bank: int
    risk: str
    probability: float
    is_top: bool = False


def window_dates(now: datetime | None = None) -> set[date]:
    current = now.astimezone(MSK) if now else datetime.now(MSK)
    start = current.date()
    return {start, start + timedelta(days=1)}


def _state(event: dict) -> str:
    status = event.get("status") if isinstance(event.get("status"), dict) else {}
    kind = status.get("type") if isinstance(status.get("type"), dict) else {}
    if kind.get("state"):
        return str(kind["state"])
    competitions = event.get("competitions") or []
    if competitions and isinstance(competitions[0], dict):
        nested = competitions[0].get("status")
        if isinstance(nested, dict) and isinstance(nested.get("type"), dict):
            return str(nested["type"].get("state") or "")
    return ""


def _teams(competition: dict) -> tuple[dict, dict] | None:
    home = away = None
    for row in competition.get("competitors") or []:
        if not isinstance(row, dict):
            continue
        if row.get("homeAway") == "home":
            home = row
        elif row.get("homeAway") == "away":
            away = row
    if home is None or away is None:
        rows = [row for row in (competition.get("competitors") or []) if isinstance(row, dict)]
        if len(rows) < 2:
            return None
        home, away = rows[0], rows[1]
    return home, away


def pick_from_event(
    event: dict,
    sport: str,
    league: str,
    allowed: set[date],
    now: datetime | None = None,
) -> PlannedPick | None:
    if _state(event) not in {"pre", ""}:
        return None
    competitions = event.get("competitions") or []
    if not competitions or not isinstance(competitions[0], dict):
        return None
    competition = competitions[0]
    raw_date = competition.get("date") or event.get("date")
    if not raw_date:
        return None
    kickoff = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).astimezone(MSK)
    current = now.astimezone(MSK) if now else datetime.now(MSK)
    # Уже начавшиеся и сыгранные матчи не публикуем: линия к этому моменту другая.
    if kickoff <= current or kickoff.date() not in allowed:
        return None
    teams = _teams(competition)
    if teams is None:
        return None
    home_row, away_row = teams
    home_team = home_row.get("team") if isinstance(home_row.get("team"), dict) else {}
    away_team = away_row.get("team") if isinstance(away_row.get("team"), dict) else {}
    home_en = str(home_team.get("displayName") or home_team.get("name") or "").strip()
    away_en = str(away_team.get("displayName") or away_team.get("name") or "").strip()
    if not home_en or not away_en:
        return None
    home = russian_team_name(home_en)
    away = russian_team_name(away_en)
    odds_list = competition.get("odds") or []
    odds = odds_list[0] if odds_list and isinstance(odds_list[0], dict) else {}
    markets = outcomes_from_espn(odds, home, away)
    chosen: Outcome | None = most_likely(markets)
    if chosen is None:
        return None
    risk, bank = risk_and_bank(chosen.probability)
    match_key = f"{sport}|{home_en.casefold()}|{away_en.casefold()}|{kickoff.date().isoformat()}"
    return PlannedPick(
        match_key=match_key,
        sport=sport,
        league=league,
        team1=home,
        team2=away,
        home_logo=str(home_team.get("logo") or ""),
        away_logo=str(away_team.get("logo") or ""),
        kickoff=kickoff,
        match_datetime=kickoff.strftime("%d.%m в %H:%M"),
        bet_type=chosen.label,
        odds=chosen.decimal,
        stake=team1_percent(markets),
        bank=bank,
        risk=risk,
        probability=round(chosen.probability, 4),
    )


def fetch_board(client: httpx.Client, sport_path: str, league_path: str, day: date) -> list[dict]:
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/{league_path}/scoreboard"
    response = client.get(url, params={"dates": day.strftime("%Y%m%d")})
    if response.status_code == 404:
        return []
    response.raise_for_status()
    payload = response.json()
    events = payload.get("events") if isinstance(payload, dict) else None
    return [event for event in events or [] if isinstance(event, dict)]


def collect_picks(client: httpx.Client, limit: int, now: datetime | None = None) -> list[PlannedPick]:
    allowed = window_dates(now)
    found: dict[str, PlannedPick] = {}
    for sport, sport_path, league_path, league_name in LEAGUES:
        for day in sorted(allowed):
            try:
                events = fetch_board(client, sport_path, league_path, day)
            except httpx.HTTPError:
                continue
            for event in events:
                pick = pick_from_event(event, sport, league_name, allowed, now)
                if pick is not None:
                    found[pick.match_key] = pick
    ordered = sorted(found.values(), key=lambda item: item.kickoff)
    trimmed = ordered[:limit]
    if not trimmed:
        return []
    top_key = max(trimmed, key=lambda item: item.probability).match_key
    return [
        PlannedPick(**{**item.__dict__, "is_top": item.match_key == top_key})
        for item in trimmed
    ]
