import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="World Cup 2026 Simulator", layout="wide")

# --- 1. DATA INGESTION (OFFICIAL 2026 GROUPS) ---
@st.cache_data
def get_official_groups():
    """The actual 12 groups for the 2026 World Cup."""
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
    """Realistic Elo ratings for the 48 qualified teams."""
    teams = [team for group in get_official_groups().values() for team in group]
    # Assigning proxy ratings based on historical global ranks
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

# --- 2. CORE LOGIC ---
def simulate_match(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def generate_predicted_bracket(elo_df, groups):
    """Predicts the knockout stage using the official FIFA 12-group structural mapping."""
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    
    # 1. Deterministic Group Stage (Rank teams by Elo to simulate expected finish)
    group_standings = {}
    third_places = []
    
    for group_letter, teams in groups.items():
        sorted_teams = sorted(teams, key=lambda x: elo_dict[x], reverse=True)
        group_standings[group_letter] = sorted_teams
        third_places.append((sorted_teams[2], elo_dict[sorted_teams[2]]))
        
    # Get top 8 third-place teams overall
    best_thirds = [t[0] for t in sorted(third_places, key=lambda x: x[1], reverse=True)[:8]]
    
    def get_3rd(pool):
        """Helper to assign a valid 3rd place team from the pool without reusing them."""
        for t in best_thirds:
            for g in pool:
                if t in group_standings[g]:
                    best_thirds.remove(t)
                    return t
        return "TBD (No valid 3rd)"

    # 2. Official Round of 32 Mapping
    r32_matches = [
        (group_standings['A'][1], group_standings['B'][1]),                         # Match 73: 2A vs 2B
        (group_standings['E'][0], get_3rd(['A','B','C','D','F'])),                  # Match 74: 1E vs 3A/B/C/D/F
        (group_standings['F'][0], group_standings['C'][1]),                         # Match 75: 1F vs 2C
        (group_standings['C'][0], group_standings['F'][1]),                         # Match 76: 1C vs 2F
        (group_standings['I'][0], get_3rd(['C','D','F','G','H'])),                  # Match 77: 1I vs 3C/D/F/G/H
        (group_standings['E'][1], group_standings['I'][1]),                         # Match 78: 2E vs 2I
        (group_standings['A'][0], get_3rd(['C','E','F','H','I'])),                  # Match 79: 1A vs 3C/E/F/H/I
        (group_standings['L'][0], get_3rd(['E','H','I','J','K'])),                  # Match 80: 1L vs 3E/H/I/J/K
        (group_standings['D'][0], get_3rd(['B','E','F','I','J'])),                  # Match 81: 1D vs 3B/E/F/I/J
        (group_standings['G'][0], get_3rd(['A','E','H','I','J'])),                  # Match 82: 1G vs 3A/E/H/I/J
        (group_standings['K'][1], group_standings['L'][1]),                         # Match 83: 2K vs 2L
        (group_standings['H'][0], group_standings['J'][1]),                         # Match 84: 1H vs 2J
        (group_standings['B'][0], get_3rd(['E','F','G','I','J'])),                  # Match 85: 1B vs 3E/F/G/I/J
        (group_standings['J'][0], group_standings['H'][1]),                         # Match 86: 1J vs 2H
        (group_standings['K'][0], get_3rd(['D','E','I','J','L'])),                  # Match 87: 1K vs 3D/E/I/J/L
        (group_standings['D'][1], group_standings['G'][1])                          # Match 88: 2D vs 2G
    ]

    bracket = {"Round of 32": [], "Round of 16": [], "Quarter-Finals": [], "Semi-Finals": [], "Final": []}
    
    # Resolve R32
    r16_teams = []
    for t1, t2 in r32_matches:
        winner = t1 if simulate_match(elo_dict.get(t1, 1500), elo_dict.get(t2, 1500)) > 0.5 else t2
        bracket["Round of 32"].append(f"{t1} vs {t2} *(Advancing: {winner})*")
        r16_teams.append(winner)

    # Official Knockout Pathing
    def simulate_deterministic_round(teams_in_round, round_name):
        next_round = []
        for i in range(0, len(teams_in_round), 2):
            t1, t2 = teams_in_round[i], teams_in_round[i+1]
            winner = t1 if simulate_match(elo_dict[t1], elo_dict[t2]) > 0.5 else t2
            bracket[round_name].append(f"{t1} vs {t2} *(Advancing: {winner})*")
            next_round.append(winner)
        return next_round

    # R16 pairings follow the official match number schedule 
    # (e.g., W73 vs W75, W74 vs W77, W76 vs W78, W79 vs W80, W83 vs W84, W81 vs W82, W86 vs W88, W85 vs W87)
    r16_ordered = [
        r16_teams[0], r16_teams[2], r16_teams[1], r16_teams[4], 
        r16_teams[3], r16_teams[5], r16_teams[6], r16_teams[7],
        r16_teams[10], r16_teams[11], r16_teams[8], r16_teams[9], 
        r16_teams[13], r16_teams[15], r16_teams[12], r16_teams[14]
    ]

    qf_teams = simulate_deterministic_round(r16_ordered, "Round of 16")
    sf_teams = simulate_deterministic_round(qf_teams, "Quarter-Finals")
    final_teams = simulate_deterministic_round(sf_teams, "Semi-Finals")
    simulate_deterministic_round(final_teams, "Final")
    
    return bracket

# --- 3. UI DASHBOARD ---
st.title("🏆 World Cup 2026 Live Probabilities")

elo_df = fetch_elo_ratings()
groups = get_official_groups()

st.header("Predicted Bracket Matchups (Official FIFA Structure)")
st.markdown("Calculated deterministically using the official 12-group format and strict Round of 32 FIFA mapping.")

bracket = generate_predicted_bracket(elo_df, groups)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.subheader("Round of 32")
    for match in bracket["Round of 32"]: st.markdown(f"- {match}")
with col2:
    st.subheader("Round of 16")
    for match in bracket["Round of 16"]: st.markdown(f"- {match}")
with col3:
    st.subheader("Quarter-Finals")
    for match in bracket["Quarter-Finals"]: st.markdown(f"- {match}")
with col4:
    st.subheader("Semi-Finals")
    for match in bracket["Semi-Finals"]: st.markdown(f"- {match}")
with col5:
    st.subheader("Final")
    for match in bracket["Final"]: st.markdown(f"- {match}")

st.divider()
st.subheader("Baseline Data (Actual 2026 Qualified Groups)")
st.json(groups)
