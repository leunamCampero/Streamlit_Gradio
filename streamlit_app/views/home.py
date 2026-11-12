import pandas as pd
import streamlit as st

from ui import network

st.title("Optimisation and comparison of urban cycling networks")
st.markdown(
    "Interactive results of the PhD thesis of **Manuel Campero Jurado** "
    "(with C. Canudas-de-Wit, G. De Nunzio and M. Salazar). "
    "Every page reads the result tables produced by the code of the thesis "
    "([PhD_tesis repository](https://github.com/leunamCampero/PhD_tesis))."
)

net = network()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Grenoble network", f"{net.N:,} nodes")
c2.metric("Edges", f"{net.E:,}")
c3.metric("Length", f"{net.length.sum() / 1000:.0f} km")
c4.metric("Cost to upgrade it all to DoS 6", f"EUR {net.max_budget() / 1e6:.1f} M")

st.subheader("The papers")
st.dataframe(pd.DataFrame([
    ["T-ITS 2025", "Graph metrics of 14 French cities, safety/comfort model, MLCC vs GA vs Bayesian opt.",
     "The largest connected safe component l_G is the metric that explains perceived safety."],
    ["ECC 2025", "Bi-level upgrade of Grenoble by degree of separation (DoS)",
     "GAB cuts cyclist exposure by 99.6 % vs 32 % for MLCC with the same budget."],
    ["CDC 2025", "Utilitarian vs sufficientarian (justice) upgrades",
     "GA-S lowers safety insufficiency 7-79 % more than GA-U at almost no exposure cost."],
    ["ITSC 2025", "Two-layer bike + car network, Pareto trade-off",
     "-90 % cyclist exposure for only +1.5-2 % car travel time after re-routing."],
    ["ITSC 2026", "Safety-aware clustering (CC) + Gromov-Wasserstein comparison",
     "CC keeps the exposure within 1-3 %; with it Strasbourg is closer to Grenoble than Lyon."],
], columns=["Paper", "Topic", "Main result"]), hide_index=True, width="stretch")

st.subheader("Key idea: degree of separation (DoS)")
st.markdown(
    "Each street segment carries a **DoS** from 1 (unmarked lane shared with cars) to 6 "
    "(fully separated bike lane). Cyclists choose routes with a *cyclist distance* that "
    "penalises slope and adjacent car traffic; the optimisation decides which segments to upgrade "
    "within a budget. Use the menu on the left to explore the network and every paper's results."
)
