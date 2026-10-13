"""Линия букмекера и выбор самого вероятного исхода внутри каждого рынка."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Outcome:
    code: str
    label: str
    decimal: float
    probability: float


def parse_american(raw: object) -> int | None:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    text = str(raw).strip().upper().replace("−", "-").replace("–", "-")
    if text in {"EVEN", "EV"}:
        return 100
    text = text.replace("+", "")
    if not text or text in {"-", "."}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def american_to_decimal(american: int) -> float:
    if american == 0:
        raise ValueError("Нулевая американская линия")
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def devig(decimals: list[float]) -> list[float]:
    raw = [1 / price for price in decimals if price > 1]
    if len(raw) != len(decimals) or not raw:
        raise ValueError("В рынке есть коэффициент не больше 1")
    total = sum(raw)
    return [item / total for item in raw]


def close_odds(node: object) -> int | None:
    if not isinstance(node, dict):
        return None
    close = node.get("close")
    if isinstance(close, dict) and close.get("odds") is not None:
        return parse_american(close.get("odds"))
    open_ = node.get("open")
    if isinstance(open_, dict):
        return parse_american(open_.get("odds"))
    return parse_american(node.get("moneyLine"))


def _market(pairs: list[tuple[str, str, int]]) -> list[Outcome]:
    decimals = [american_to_decimal(price) for _, _, price in pairs]
    probs = devig(decimals)
    return [
        Outcome(code=code, label=label, decimal=round(decimal, 2), probability=prob)
        for (code, label, _), decimal, prob in zip(pairs, decimals, probs, strict=True)
    ]


def outcomes_from_espn(
    odds: dict,
    home: str,
    away: str,
) -> dict[str, list[Outcome]]:
    markets: dict[str, list[Outcome]] = {}
    moneyline = odds.get("moneyline") if isinstance(odds.get("moneyline"), dict) else {}
    sides: list[tuple[str, str, int]] = []
    for code, label, key in (
        ("home", f"Победа {home}", "home"),
        ("draw", "Ничья", "draw"),
        ("away", f"Победа {away}", "away"),
    ):
        price = close_odds(moneyline.get(key))
        if price is None and key == "draw":
            price = close_odds(odds.get("drawOdds"))
        if price is not None:
            sides.append((code, label, price))
    if len(sides) >= 2:
        markets["result"] = _market(sides)

    total = odds.get("total") if isinstance(odds.get("total"), dict) else {}
    line = odds.get("overUnder")
    over = close_odds(total.get("over"))
    under = close_odds(total.get("under"))
    if line is not None and over is not None and under is not None:
        line_text = str(line).rstrip("0").rstrip(".") if isinstance(line, float) else str(line)
        markets["total"] = _market(
            [
                ("over", f"Тотал больше {line_text}", over),
                ("under", f"Тотал меньше {line_text}", under),
            ]
        )
    return markets


def most_likely(markets: dict[str, list[Outcome]]) -> Outcome | None:
    chosen: Outcome | None = None
    for market in markets.values():
        for outcome in market:
            if chosen is None or outcome.probability > chosen.probability:
                chosen = outcome
    return chosen


def team1_percent(markets: dict[str, list[Outcome]]) -> int:
    result = markets.get("result") or []
    home = next((item.probability for item in result if item.code == "home"), None)
    away = next((item.probability for item in result if item.code == "away"), None)
    if home is None:
        return 50
    if away is None:
        return max(1, min(99, round(home * 100)))
    share = home / (home + away)
    return max(1, min(99, round(share * 100)))


def risk_and_bank(probability: float) -> tuple[str, int]:
    if probability >= 0.62:
        return "low", 3
    if probability >= 0.54:
        return "medium", 2
    return "high", 1
