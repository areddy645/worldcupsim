import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="World Cup 2026 Simulator", layout="wide")

# --- 1. DATA INGESTION (OFFICIAL 2026 GROUPS) ---
@st.cache_data
def get_official_groups():
    return {
        "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
        "B": ["Switzerland", "Canada", "Bosnia and Herzegovina", "Qatar"],
        "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
        "D": ["USA", "Australia", "Paraguay", "Türkiye"],
        "E": ["Germany", "Ivory Coast", "Ecuador", "Curaçao"],
        "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
        "G": ["Egypt", "Iran", "Belgium", "New Zealand"],
        "H": ["Spain", "Uruguay", "Cabo Verde", "Saudi Arabia"],
        "I": ["France", "Norway", "Senegal", "Iraq"],
        "J": ["Argentina", "Austria", "Algeria", "Jordan"],
        "K": ["Colombia", "Portugal", "DR Congo", "Uzbekistan"],
        "L": ["England", "Ghana", "Croatia", "Panama"]
    }

@st.cache_data
def fetch_elo_ratings():
    groups = get_official_groups()
    teams = [team for group in groups.values() for team in group]
    
    base_ratings = {
        "Argentina": 2140, "France": 2110, "Spain": 2090, "England": 2040, "Brazil": 2030,
        "Portugal": 2010, "Netherlands": 2000, "Colombia": 1990, "Germany": 1970, "Uruguay": 1960, 
        "Croatia": 1950, "Belgium": 1930, "Morocco": 1910, "Japan": 1890, "USA": 1880, 
        "Mexico": 1870, "Senegal": 1860, "Switzerland": 1850, "Ecuador": 1830, "Iran": 1810, 
        "South Korea": 1800, "Austria": 1790, "Australia": 1780, "Sweden": 1740, "Türkiye": 1735,
        "Scotland": 1720, "Norway": 1715, "South Africa": 1700, "Ivory Coast": 1690, "Egypt": 1685,
        "Canada": 1650, "Czechia": 1640, "Paraguay": 1630, "Algeria": 1620, "Tunisia": 1610,
        "Panama": 1600, "Bosnia and Herzegovina": 1590, "Ghana": 1580, "Qatar": 1570, "Saudi Arabia": 1560,
        "Iraq": 1550, "New Zealand": 1540, "Cabo Verde": 1530, "Haiti": 1520, "Jordan": 1510,
        "DR Congo": 1500, "Uzbekistan": 1490, "Curaçao": 1480
    }
    return pd.DataFrame([{"Team": t, "Elo": base_ratings.get(t, 1500)} for t in teams])

# --- 2. MATCH SIMULATION & BRACKET MAPPING LOGIC ---
def simulate_match_prob(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def run_tournament(elo_dict, groups, deterministic=False):
    """Simulates or deterministically calculates one full tournament run based on the official FIFA bracket."""
    group_standings = {}
    third_places = []
    
    # 1. Group Stage
    for group_letter, teams in groups.items():
        if deterministic:
            # Sort directly by Elo
            sorted_teams = sorted(teams, key=lambda x: elo_dict[x], reverse=True)
        else:
            pts = {t: 0 for t in teams}
            for i in range(len(teams)):
                for j in range(i+1, len(teams)):
                    t1, t2 = teams[i], teams[j]
                    p_win = simulate_match_prob(elo_dict[t1], elo_dict[t2])
                    roll = np.random.rand()
                    if roll < p_win * 0.75: pts[t1] += 3
                    elif roll > 1 - ((1-p_win)*0.75): pts[t2] += 3
                    else: pts[t1] += 1; pts[t2] += 1
            sorted_teams = [t[0] for t in sorted(pts.items(), key=lambda x: (x[1], elo_dict[x[0]]), reverse=True)]
            
        group_standings[group_letter] = sorted_teams
        third_places.append((group_letter, sorted_teams[2], elo_dict[sorted_teams[2]]))

    # 2. Select the best 8 third-place teams
    if deterministic:
        best_thirds = sorted(third_places, key=lambda x: x[2], reverse=True)[:8]
    else:
        # In monte carlo, we simulate points roughly, but using elo as a proxy tiebreaker
        best_thirds = sorted(third_places, key=lambda x: x[2], reverse=True)[:8] 
        
    third_teams_dict = {g: t for g, t, e in best_thirds}

    def get_3rd(valid_groups):
        """Finds an available 3rd place team from the allowed source groups."""
        for g in valid_groups:
            if g in third_teams_dict:
                team = third_teams_dict.pop(g)
                return team
        # Fallback if the strict matrix combinations run dry (happens rarely in simplified dynamic mapping)
        if third_teams_dict:
            k = list(third_teams_dict.keys())[0]
            return third_teams_dict.pop(k)
        return "Unknown"

    # 3. Official FIFA Round of 32 (Matches 73-88)
    r32_matches = [
        (group_standings['A'][1], group_standings['B'][1]),                         # M73: 2A v 2B
        (group_standings['E'][0], get_3rd(['A','B','C','D','F'])),                  # M74: 1E v 3rd
        (group_standings['F'][0], group_standings['C'][1]),                         # M75: 1F v 2C
        (group_standings['C'][0], group_standings['F'][1]),                         # M76: 1C v 2F
        (group_standings['I'][0], get_3rd(['C','D','F','G','H'])),                  # M77: 1I v 3rd
        (group_standings['E'][1], group_standings['I'][1]),                         # M78: 2E v 2I
        (group_standings['A'][0], get_3rd(['C','E','F','H','I'])),                  # M79: 1A v 3rd
        (group_standings['L'][0], get_3rd(['E','H','I','J','K'])),                  # M80: 1L v 3rd
        (group_standings['D'][0], get_3rd(['B','E','F','I','J'])),                  # M81: 1D v 3rd
        (group_standings['G'][0], get_3rd(['A','E','H','I','J'])),                  # M82: 1G v 3rd
        (group_standings['K'][1], group_standings['L'][1]),                         # M83: 2K v 2L
        (group_standings['H'][0], group_standings['J'][1]),                         # M84: 1H v 2J
        (group_standings['B'][0], get_3rd(['E','F','G','I','J'])),                  # M85: 1B v 3rd
        (group_standings['J'][0], group_standings['H'][1]),                         # M86: 1J v 2H
        (group_standings['K'][0], get_3rd(['D','E','I','J','L'])),                  # M87: 1K v 3rd
        (group_standings['D'][1], group_standings['G'][1])                          # M88: 2D v 2G
    ]

    bracket = {"Round of 32": [], "Round of 16": [], "Quarter-Finals": [], "Semi-Finals": [], "Final": []}
    
    def play_match(t1, t2, round_name=None):
        if deterministic:
            winner = t1 if elo_dict.get(t1, 1500) > elo_dict.get(t2, 1500) else t2
        else:
            winner = t1 if np.random.rand() < simulate_match_prob(elo_dict.get(t1, 1500), elo_dict.get(t2, 1500)) else t2
        
        if round_name:
            bracket[round_name].append(f"{t1} vs {t2} *(Adv: {winner})*")
        return winner

    # R32 Results
    m = {}
    for i, match in enumerate(r32_matches):
        m[73+i] = play_match(match[0], match[1], "Round of 32" if deterministic else None)

    # 4. Official FIFA Round of 16 (Matches 89-96)
    r16_matches = [
        (m[74], m[77]), (m[73], m[75]), (m[76], m[78]), (m[79], m[80]), # M89, M90, M91, M92
        (m[83], m[84]), (m[81], m[82]), (m[86], m
