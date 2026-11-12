"""
Entry point of the Streamlit dashboard.

    streamlit run streamlit_app/app.py

Streamlit re-runs this script from top to bottom every time the user touches a widget.
``st.navigation`` picks which page script (in ``views/``) is shown.
"""
import sys
from pathlib import Path

import streamlit as st

# Make the shared ``core`` package (repo root) importable from every page.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

st.set_page_config(page_title="Cycling networks - PhD results", page_icon=":bike:", layout="wide")

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("views/network.py", title="Network explorer", icon=":material/map:"),
        st.Page("views/model.py", title="Cyclist-distance model", icon=":material/tune:"),
    ],
    "Results per paper": [
        st.Page("views/tits2025.py", title="T-ITS 2025 - 14 cities", icon=":material/scatter_plot:"),
        st.Page("views/ecc2025.py", title="ECC 2025 - GAB vs MLCC", icon=":material/compare_arrows:"),
        st.Page("views/cdc2025.py", title="CDC 2025 - Justice", icon=":material/balance:"),
        st.Page("views/itsc2025.py", title="ITSC 2025 - Bikes vs cars", icon=":material/directions_car:"),
        st.Page("views/itsc2026.py", title="ITSC 2026 - Clustering", icon=":material/hub:"),
    ],
}
st.navigation(pages).run()
