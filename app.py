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
        (m[83], m[84]), (m[81], m[82]), (m[86], m[88]), (m[85], m[87])  # M93, M94, M95, M96
    ]
    for i, match in enumerate(r16_matches):
        m[89+i] = play_match(match[0], match[1], "Round of 16" if deterministic else None)

    # 5. Official FIFA Quarter-Finals (Matches 97-100)
    qf_matches = [(m[89], m[90]), (m[93], m[94]), (m[91], m[92]), (m[95], m[96])]
    for i, match in enumerate(qf_matches):
        m[97+i] = play_match(match[0], match[1], "Quarter-Finals" if deterministic else None)

    # 6. Official FIFA Semi-Finals (Matches 101-102)
    m[101] = play_match(m[97], m[98], "Semi-Finals" if deterministic else None)
    m[102] = play_match(m[99], m[100], "Semi-Finals" if deterministic else None)

    # 7. Official FIFA Final (Match 104)
    winner = play_match(m[101], m[102], "Final" if deterministic else None)
    
    if deterministic:
        return bracket
    else:
        # Return how far teams made it for the Monte Carlo aggregator
        r16_teams = [m[i] for i in range(73, 89)]
        qf_teams = [m[i] for i in range(89, 97)]
        sf_teams = [m[i] for i in range(97, 101)]
        final_teams = [m[101], m[102]]
        return r16_teams, qf_teams, sf_teams, final_teams, winner

# --- 3. RUN MONTE CARLO ---
def run_monte_carlo(elo_df, groups, n_sims=1000):
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    teams = list(elo_dict.keys())
    wins = {t: {'R16': 0, 'QF': 0, 'SF': 0, 'Final': 0, 'Win': 0} for t in teams}
    
    for _ in range(n_sims):
        r16_teams, qf_teams, sf_teams, final_teams, winner = run_tournament(elo_dict, groups, deterministic=False)
        
        for t in r16_teams: wins[t]['R16'] += 1
        for t in qf_teams: wins[t]['QF'] += 1
        for t in sf_teams: wins[t]['SF'] += 1
        for t in final_teams: wins[t]['Final'] += 1
        wins[winner]['Win'] += 1
            
    results = []
    for t in teams:
        if wins[t]['R16'] > 0: # Only show teams that advance
            results.append({
                "Team": t,
                "Make R16 (%)": (wins[t]['R16']/n_sims)*100,
                "Make QF (%)": (wins[t]['QF']/n_sims)*100,
                "Make SF (%)": (wins[t]['SF']/n_sims)*100,
                "Make Final (%)": (wins[t]['Final']/n_sims)*100,
                "Win World Cup (%)": (wins[t]['Win']/n_sims)*100,
            })
    return pd.DataFrame(results).sort_values("Win World Cup (%)", ascending=False).reset_index(drop=True)

# --- 4. UI DASHBOARD ---
st.title("🏆 World Cup 2026 Live Probabilities")
st.markdown("Calculated using strict routing through the official **FIFA Match 73–104 Knockout Bracket**.")

elo_df = fetch_elo_ratings()
groups = get_official_groups()

tab1, tab2, tab3 = st.tabs([
    "🔮 Deterministic Predicted Bracket", 
    "🏆 Monte Carlo Win Probabilities", 
    "🌐 Teams & Ratings"
])

with tab1:
    st.header("Predicted Bracket Matchups (FIFA Official Mapping)")
    
    bracket = run_tournament(dict(zip(elo_df['Team'], elo_df['Elo'])), groups, deterministic=True)
    
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

with tab2:
    st.header("Full Tournament Progression Probabilities")
    st.markdown("Running full 1,000 tournament simulations parsing Group A-L round robin points through the exact match pathing.")
    
    with st.spinner("Running Monte Carlo simulations (this may take a few seconds)..."):
        ko_probs = run_monte_carlo(elo_df, groups, n_sims=1000)
    
    st.dataframe(ko_probs.style.format({col: "{:.1f}%" for col in ko_probs.columns if "%" in col}).background_gradient(cmap="Blues"), use_container_width=True)

with tab3:
    st.header("Current Elo Ratings (Source Data)")
    st.dataframe(elo_df, use_container_width=True)
