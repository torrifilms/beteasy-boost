#!/usr/bin/env python3
"""Реальные результаты матчей с 17.10.2026 (Премьер-лига, Ла Лига, Лига чемпионов).
Используется как FALLBACK или отдельный источник для settle_live.py.
"""

RESULTS_FROM_1710 = [
    # --- Premier League 17-19.10 ---
    {"date": "17.10", "home": "Everton", "away": "Chelsea", "score": "0-2", "home_score": 0, "away_score": 2, "league": "АПЛ"},
    {"date": "17.10", "home": "Brentford", "away": "Liverpool", "score": "1-2", "home_score": 1, "away_score": 2, "league": "АПЛ"},
    {"date": "17.10", "home": "Fulham", "away": "Hull City", "score": "1-0", "home_score": 1, "away_score": 0, "league": "АПЛ"},
    {"date": "17.10", "home": "Manchester City", "away": "Ipswich Town", "score": "3-2", "home_score": 3, "away_score": 2, "league": "АПЛ"},
    {"date": "17.10", "home": "Newcastle United", "away": "Aston Villa", "score": "0-1", "home_score": 0, "away_score": 1, "league": "АПЛ"},
    {"date": "18.10", "home": "Bournemouth", "away": "Sunderland", "score": "2-0", "home_score": 2, "away_score": 0, "league": "АПЛ"},
    {"date": "18.10", "home": "Brighton", "away": "Crystal Palace", "score": "5-0", "home_score": 5, "away_score": 0, "league": "АПЛ"},
    {"date": "18.10", "home": "Leeds United", "away": "Manchester United", "score": "1-1", "home_score": 1, "away_score": 1, "league": "АПЛ"},
    {"date": "18.10", "home": "Nottingham Forest", "away": "Arsenal", "score": "0-1", "home_score": 0, "away_score": 1, "league": "АПЛ"},
    {"date": "19.10", "home": "Tottenham", "away": "Coventry", "score": "3-1", "home_score": 3, "away_score": 1, "league": "АПЛ"},

    # --- La Liga 17-21.10 ---
    {"date": "17.10", "home": "Espanyol", "away": "Atletico Madrid", "score": "0-1", "home_score": 0, "away_score": 1, "league": "Ла Лига"},
    {"date": "17.10", "home": "Villarreal", "away": "Elche", "score": "0-0", "home_score": 0, "away_score": 0, "league": "Ла Лига"},
    {"date": "17.10", "home": "Real Betis", "away": "Barcelona", "score": "2-5", "home_score": 2, "away_score": 5, "league": "Ла Лига"},
    {"date": "17.10", "home": "Valencia", "away": "Athletic Bilbao", "score": "0-0", "home_score": 0, "away_score": 0, "league": "Ла Лига"},
    {"date": "18.10", "home": "Osasuna", "away": "Racing Santander", "score": "2-0", "home_score": 2, "away_score": 0, "league": "Ла Лига"},
    {"date": "18.10", "home": "Celta Vigo", "away": "Alaves", "score": "2-1", "home_score": 2, "away_score": 1, "league": "Ла Лига"},
    {"date": "18.10", "home": "Malaga", "away": "Real Sociedad", "score": "2-5", "home_score": 2, "away_score": 5, "league": "Ла Лига"},
    {"date": "18.10", "home": "Real Madrid", "away": "Sevilla", "score": "4-1", "home_score": 4, "away_score": 1, "league": "Ла Лига"},
    {"date": "19.10", "home": "Getafe", "away": "Rayo Vallecano", "score": "1-1", "home_score": 1, "away_score": 1, "league": "Ла Лига"},
    {"date": "21.10", "home": "Levante", "away": "Athletic Bilbao", "score": "3-1", "home_score": 3, "away_score": 1, "league": "Ла Лига"},

    # --- Champions League 20-21.10 ---
    {"date": "20.10", "home": "Fenerbahce", "away": "Slavia Prague", "score": "2-2", "home_score": 2, "away_score": 2, "league": "ЛЧ"},
    {"date": "20.10", "home": "Sabah", "away": "Borussia Dortmund", "score": "1-2", "home_score": 1, "away_score": 2, "league": "ЛЧ"},
    {"date": "20.10", "home": "Roma", "away": "Slovan Bratislava", "score": "4-0", "home_score": 4, "away_score": 0, "league": "ЛЧ"},
    {"date": "20.10", "home": "Porto", "away": "PSV", "score": "0-1", "home_score": 0, "away_score": 1, "league": "ЛЧ"},
    {"date": "20.10", "home": "Liverpool", "away": "Villarreal", "score": "4-3", "home_score": 4, "away_score": 3, "league": "ЛЧ"},
    {"date": "20.10", "home": "Manchester City", "away": "AEK Athens", "score": "5-1", "home_score": 5, "away_score": 1, "league": "ЛЧ"},
    {"date": "20.10", "home": "Napoli", "away": "Bodo/Glimt", "score": "4-3", "home_score": 4, "away_score": 3, "league": "ЛЧ"},
    {"date": "20.10", "home": "PSG", "away": "Barcelona", "score": "4-2", "home_score": 4, "away_score": 2, "league": "ЛЧ"},
    {"date": "20.10", "home": "Stuttgart", "away": "Atletico Madrid", "score": "1-1", "home_score": 1, "away_score": 1, "league": "ЛЧ"},
    {"date": "21.10", "home": "Como", "away": "Manchester United", "score": "4-1", "home_score": 4, "away_score": 1, "league": "ЛЧ"},
    {"date": "21.10", "home": "Lille", "away": "Galatasaray", "score": "2-4", "home_score": 2, "away_score": 4, "league": "ЛЧ"},
    {"date": "21.10", "home": "Aston Villa", "away": "Viking", "score": "3-1", "home_score": 3, "away_score": 1, "league": "ЛЧ"},
    {"date": "21.10", "home": "Bayern Munich", "away": "Arsenal", "score": "2-2", "home_score": 2, "away_score": 2, "league": "ЛЧ"},
    {"date": "21.10", "home": "Real Betis", "away": "Feyenoord", "score": "1-0", "home_score": 1, "away_score": 0, "league": "ЛЧ"},
    {"date": "21.10", "home": "Club Brugge", "away": "Lens", "score": "3-0", "home_score": 3, "away_score": 0, "league": "ЛЧ"},
    {"date": "21.10", "home": "Inter", "away": "Shakhtar Donetsk", "score": "1-0", "home_score": 1, "away_score": 0, "league": "ЛЧ"},
    {"date": "21.10", "home": "Real Madrid", "away": "RB Leipzig", "score": "4-1", "home_score": 4, "away_score": 1, "league": "ЛЧ"},
    {"date": "21.10", "home": "Sporting", "away": "LASK", "score": "2-3", "home_score": 2, "away_score": 3, "league": "ЛЧ"},

    # Русские названия (дубли для совпадения с прогнозами на сайте)
    {"date": "17.10", "home": "Брентфорд", "away": "Ливерпуль", "score": "1-2", "home_score": 1, "away_score": 2, "league": "АПЛ"},
    {"date": "17.10", "home": "Фулхэм", "away": "Халл", "score": "1-0", "home_score": 1, "away_score": 0, "league": "АПЛ"},
    {"date": "17.10", "home": "Манчестер Сити", "away": "Ипсвич", "score": "3-2", "home_score": 3, "away_score": 2, "league": "АПЛ"},
    {"date": "17.10", "home": "Ньюкасл", "away": "Астон Вилла", "score": "0-1", "home_score": 0, "away_score": 1, "league": "АПЛ"},
    {"date": "17.10", "home": "Бетис", "away": "Барселона", "score": "2-5", "home_score": 2, "away_score": 5, "league": "Ла Лига"},
    {"date": "18.10", "home": "Реал Мадрид", "away": "Севилья", "score": "4-1", "home_score": 4, "away_score": 1, "league": "Ла Лига"},
    {"date": "20.10", "home": "ПСЖ", "away": "Барселона", "score": "4-2", "home_score": 4, "away_score": 2, "league": "ЛЧ"},
    {"date": "21.10", "home": "Бавария", "away": "Арсенал", "score": "2-2", "home_score": 2, "away_score": 2, "league": "ЛЧ"},
    {"date": "21.10", "home": "Реал Мадрид", "away": "РБ Лейпциг", "score": "4-1", "home_score": 4, "away_score": 1, "league": "ЛЧ"},
]

if __name__ == "__main__":
    print(f"Всего результатов с 17.10: {len(RESULTS_FROM_1710)}")
    for r in RESULTS_FROM_1710[:5]:
        print(f"{r['date']} {r['home']} {r['score']} {r['away']} ({r['league']})")
