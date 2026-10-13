import json
import unittest
from pathlib import Path

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from eb_predictions.matches import pick_from_event, window_dates
from eb_predictions.names import russian_team_name
from eb_predictions.odds import american_to_decimal, devig, most_likely, outcomes_from_espn, parse_american


class OddsTest(unittest.TestCase):
    def test_american_parser(self) -> None:
        self.assertEqual(parse_american("+175"), 175)
        self.assertEqual(parse_american("-115"), -115)
        self.assertEqual(parse_american("EVEN"), 100)
        self.assertIsNone(parse_american("нет"))

    def test_decimal_and_devig(self) -> None:
        self.assertAlmostEqual(american_to_decimal(-200), 1.5)
        self.assertAlmostEqual(american_to_decimal(150), 2.5)
        probs = devig([2.0, 2.0])
        self.assertAlmostEqual(sum(probs), 1)
        self.assertAlmostEqual(probs[0], 0.5)

    def test_most_likely_is_the_shorter_price(self) -> None:
        markets = outcomes_from_espn(
            {
                "moneyline": {
                    "home": {"close": {"odds": "+175"}},
                    "away": {"close": {"odds": "-150"}},
                },
                "overUnder": 2.5,
                "total": {
                    "over": {"close": {"odds": "-115"}},
                    "under": {"close": {"odds": "-105"}},
                },
            },
            "Хозяева",
            "Гости",
        )
        chosen = most_likely(markets)
        self.assertIsNotNone(chosen)
        assert chosen is not None
        self.assertEqual(chosen.code, "away")
        self.assertGreater(chosen.probability, 0.5)
        self.assertIn("Гости", chosen.label)

    def test_saved_espn_event_keeps_prematch_only_when_date_matches(self) -> None:
        sample = Path("/tmp/espn.json")
        if not sample.exists():
            self.skipTest("нет сохранённого ответа ESPN")
        event = json.loads(sample.read_text())["events"][0]
        allowed = window_dates()
        # Дата фикстуры может быть вне окна. Подменяем дату на сегодняшнее окно через kickoff check:
        kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
        pick = pick_from_event(
            event,
            "football",
            "АПЛ",
            {date.fromisoformat(event["date"][:10])},
            now=kickoff - timedelta(hours=2),
        )
        self.assertIsNotNone(pick)
        assert pick is not None
        self.assertEqual(pick.team1, russian_team_name("Crystal Palace"))
        self.assertIn(pick.bet_type, {item.label for market in outcomes_from_espn(
            event["competitions"][0]["odds"][0], pick.team1, pick.team2
        ).values() for item in market})
        self.assertTrue(allowed)

    def test_started_match_is_not_published_and_names_are_russian(self) -> None:
        event = {
            "date": "2026-10-10T13:30:00Z",
            "status": {"type": {"state": "pre"}},
            "competitions": [
                {
                    "date": "2026-10-10T13:30:00Z",
                    "competitors": [
                        {"homeAway": "home", "team": {"displayName": "Chelsea"}},
                        {"homeAway": "away", "team": {"displayName": "Manchester United"}},
                    ],
                    "odds": [
                        {
                            "moneyline": {
                                "home": {"close": {"odds": "-150"}},
                                "away": {"close": {"odds": "+175"}},
                            },
                            "overUnder": 2.5,
                            "total": {
                                "over": {"close": {"odds": "-110"}},
                                "under": {"close": {"odds": "-110"}},
                            },
                        }
                    ],
                }
            ],
        }
        allowed = {date(2026, 10, 10)}
        msk = ZoneInfo("Europe/Moscow")
        self.assertIsNone(
            pick_from_event(event, "football", "АПЛ", allowed, now=datetime(2026, 10, 10, 18, 0, tzinfo=msk))
        )
        pick = pick_from_event(event, "football", "АПЛ", allowed, now=datetime(2026, 10, 10, 12, 0, tzinfo=msk))
        self.assertIsNotNone(pick)
        assert pick is not None
        self.assertEqual(pick.team1, "Челси")
        self.assertEqual(pick.team2, "Манчестер Юнайтед")
        self.assertIn("Челси", pick.bet_type)


if __name__ == "__main__":
    unittest.main()
