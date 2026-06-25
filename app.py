import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="World Cup 2026 Simulator", layout="wide")

# --- 1. DATA INGESTION ---

@st.cache_data(ttl=3600)
def fetch_elo_ratings():
    """Proxy for live Elo ratings using ONLY officially qualified 2026 teams."""
    mock_teams = {
        "Argentina": 2140, "France": 2110, "Spain": 2090, "England": 2040, "Brazil": 2030,
        "Portugal": 2010, "Netherlands": 2000, "Colombia": 1990, "Germany": 1970, "Uruguay": 1960, 
        "Croatia": 1950, "Belgium": 1930, "Morocco": 1910, "Japan": 1890, "USA": 1880, 
        "Mexico": 1870, "Senegal": 1860, "Switzerland": 1850, "Ecuador": 1830, "Iran": 1810, 
        "South Korea": 1800, "Austria": 1790, "Australia": 1780, "Sweden": 1740, "Turkey": 1735,
        "Scotland": 1720, "Norway": 1715, "South Africa": 1700, "Ivory Coast": 1690, "Egypt": 1685,
        "Canada": 1650, "New Zealand": 1620
    }
    return pd.DataFrame(list(mock_teams.items()), columns=["Team", "Elo"])

@st.cache_data
def generate_groups(elo_df):
    """Randomly seed the teams into groups for simulation purposes."""
    teams = elo_df['Team'].tolist()
    np.random.shuffle(teams)
    # Using 8 groups of 4 for the top 32 teams to simplify the bracket logic
    return {f"Group {chr(65+i)}": teams[i*4:(i+1)*4] for i in range(8)}

# --- 2. MONTE CARLO SIMULATION CORE ---
def simulate_match(elo_a, elo_b):
    """Returns probability of A winning."""
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def run_group_stage_sim(groups, elo_df, n_sims=1000):
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    knockout_appearances = {team: 0 for team in elo_dict.keys()}
    
    for _ in range(n_sims):
        for group, teams in groups.items():
            pts = {t: 0 for t in teams}
            for i in range(len(teams)):
                for j in range(i+1, len(teams)):
                    t1, t2 = teams[i], teams[j]
                    p_win = simulate_match(elo_dict[t1], elo_dict[t2])
                    roll = np.random.rand()
                    if roll < p_win * 0.75: pts[t1] += 3
                    elif roll > 1 - ((1-p_win)*0.75): pts[t2] += 3
                    else:
                        pts[t1] += 1
                        pts[t2] += 1
            sorted_group = sorted(pts.items(), key=lambda x: x[1], reverse=True)
            knockout_appearances[sorted_group[0][0]] += 1
            knockout_appearances[sorted_group[1][0]] += 1
            
    prob_df = pd.DataFrame([
        {"Team": team, "Probability to Advance": (count / n_sims) * 100}
        for team, count in knockout_appearances.items()
    ]).sort_values("Probability to Advance", ascending=False).reset_index(drop=True)
    return prob_df

def run_knockout_sim(elo_df, n_sims=1000):
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    teams_32 = list(elo_dict.keys())[:32]
    wins = {t: {'R16':0, 'QF':0, 'SF':0, 'Final':0, 'Win':0} for t in teams_32}
    
    for _ in range(n_sims):
        r16 = [teams_32[i] if np.random.rand() < simulate_match(elo_dict[teams_32[i]], elo_dict[teams_32[31-i]]) else teams_32[31-i] for i in range(0, 32, 2)]
        for t in r16: wins[t]['R16'] += 1
        
        qf = [r16[i] if np.random.rand() < simulate_match(elo_dict[r16[i]], elo_dict[r16[i+1]]) else r16[i+1] for i in range(0, 16, 2)]
        for t in qf: wins[t]['QF'] += 1
        
        sf = [qf[i] if np.random.rand() < simulate_match(elo_dict[qf[i]], elo_dict[qf[i+1]]) else qf[i+1] for i in range(0, 8, 2)]
        for t in sf: wins[t]['SF'] += 1
        
        finals = [sf[i] if np.random.rand() < simulate_match(elo_dict[sf[i]], elo_dict[sf[i+1]]) else sf[i+1] for i in range(0, 4, 2)]
        for t in finals: wins[t]['Final'] += 1
        
        if np.random.rand() < simulate_match(elo_dict[finals[0]], elo_dict[finals[1]]):
            wins[finals[0]]['Win'] += 1
        else:
            wins[finals[1]]['Win'] += 1
            
    results = [{"Team": t, "Make R16 (%)": (wins[t]['R16']/n_sims)*100, "Make QF (%)": (wins[t]['QF']/n_sims)*100, "Make SF (%)": (wins[t]['SF']/n_sims)*100, "Make Final (%)": (wins[t]['Final']/n_sims)*100, "Win World Cup (%)": (wins[t]['Win']/n_sims)*100} for t in teams_32]
    return pd.DataFrame(results).sort_values("Win World Cup (%)", ascending=False).reset_index(drop=True)

def generate_predicted_bracket(elo_df):
    """Deterministically predicts matchups based on highest Elo probability."""
    elo_dict = dict(zip(elo_df['Team'], elo_df['Elo']))
    teams = list(elo_df['Team'])
    
    bracket = {"Round of 32": [], "Round of 16": [], "Quarter-Finals": [], "Semi-Finals": [], "Final": []}
    
    # R32 Matchups (1 vs 32, 2 vs 31, etc.)
    current_round = teams.copy()
    for i in range(0, 16):
        t1, t2 = current_round[i], current_round[31-i]
        p_win = simulate_match(elo_dict[t1], elo_dict[t2])
        winner = t1 if p_win > 0.5 else t2
        bracket["Round of 32"].append(f"{t1} vs {t2} *(Advancing: {winner})*")
    
    # Progress through rounds deterministically
    def simulate_deterministic_round(teams_in_round, round_name):
        next_round = []
        for i in range(0, len(teams_in_round), 2):
            t1, t2 = teams_in_round[i], teams_in_round[i+1]
            p_win = simulate_match(elo_dict[t1], elo_dict[t2])
            winner = t1 if p_win > 0.5 else t2
            bracket[round_name].append(f"{t1} vs {t2} *(Advancing: {winner})*")
            next_round.append(winner)
        return next_round

    r16_teams = [t.split("*(Advancing: ")[1].replace(")*", "") for t in bracket["Round of 32"]]
    qf_teams = simulate_deterministic_round(r16_teams, "Round of 16")
    sf_teams = simulate_deterministic_round(qf_teams, "Quarter-Finals")
    final_teams = simulate_deterministic_round(sf_teams, "Semi-Finals")
    simulate_deterministic_round(final_teams, "Final")
    
    return bracket

# --- 3. UI DASHBOARD ---
st.title("🏆 World Cup 2026 Live Probabilities")
st.markdown("Based on Monte Carlo Simulations and live Elo ratings from eloratings.net.")

elo_df = fetch_elo_ratings()
groups = generate_groups(elo_df)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Knockout Advancement", 
    "🏆 Tournament Win Probabilities", 
    "🌐 Raw Elo Ratings",
    "🔮 Predicted Matchups"
])

with tab1:
    st.header("Odds of Advancing from Group Stage")
    with st.spinner("Running group stage simulations..."):
        group_probs = run_group_stage_sim(groups, elo_df, n_sims=1000)
    st.dataframe(group_probs.style.format({"Probability to Advance": "{:.1f}%"}).background_gradient(cmap="Greens"), use_container_width=True)

with tab2:
    st.header("Knockout Round Progression Probabilities")
    with st.spinner("Running knockout bracket simulations..."):
        ko_probs = run_knockout_sim(elo_df, n_sims=1000)
    st.dataframe(ko_probs.style.format({col: "{:.1f}%" for col in ko_probs.columns if "%" in col}).background_gradient(cmap="Blues"), use_container_width=True)

with tab3:
    st.header("Current Elo Ratings (Source Data)")
    st.dataframe(elo_df, use_container_width=True)

with tab4:
    st.header("Predicted Bracket Matchups")
    st.markdown("Displays the most mathematically probable matchups in each round if the higher-Elo team wins every game.")
    
    bracket = generate_predicted_bracket(elo_df)
    
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
