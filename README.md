# Cycling networks — interactive PhD results (Streamlit + Gradio)

Two interactive web apps presenting the results of the PhD thesis
*Optimisation and comparison of urban cycling networks* (Manuel Campero Jurado, with
C. Canudas-de-Wit, G. De Nunzio and M. Salazar). The code and data of the papers are in
[PhD_tesis](https://github.com/leunamCampero/PhD_tesis); this repository only contains the result
tables and the Grenoble network needed by the apps (~0.7 MB).

| App | What it shows |
|---|---|
| **Streamlit dashboard** (`streamlit_app/`) | One page per paper (T-ITS 2025, ECC 2025, CDC 2025, ITSC 2025, ITSC 2026) with interactive charts, a map explorer of today's and the optimised Grenoble networks, and a playground for the cyclist-distance model and upgrade costs. |
| **Gradio route planner** (`gradio_app/`) | Pick two Grenoble neighbourhoods and a network: compares the *safest* route (cyclist distance) with the *shortest* one, shows the same trip on every optimised network, and predicts perceived safety from the network metric l_G. |

## Run it

```bash
git clone https://github.com/leunamCampero/Streamlit_Gradio.git
cd Streamlit_Gradio

# 1. create a virtual environment (once)
python -m venv .venv

# 2. activate it (every new terminal)
.venv\Scripts\activate            # Windows (PowerShell / cmd)
source .venv/bin/activate         # macOS / Linux / Git Bash on Windows: source .venv/Scripts/activate

# 3. install the packages (once)
pip install -r requirements.txt

# 4. start an app
streamlit run streamlit_app/app.py     # -> http://localhost:8501
python gradio_app/app.py               # -> http://127.0.0.1:7860
```

Tests (every Streamlit page is rendered headlessly + checks against the papers' numbers):

```bash
python -m pytest tests -q
```

## Layout

```
Streamlit_Gradio/
├── core/cycling.py          the model shared by both apps: traffic factor, slope factor,
│                            cyclist distance, Cerema costs, Dijkstra routing, optimised networks
├── streamlit_app/
│   ├── app.py               entry point + navigation (st.navigation)
│   ├── ui.py                cached data loading and the network map
│   └── views/               one script per page
├── gradio_app/app.py        route planner (gr.Blocks)
├── data/
│   ├── network/             Grenoble: 3,452 nodes, 4,993 edges with DoS, length, slope; 70 IRIS
│   ├── solutions/           DoS of every edge in the optimised networks of ECC/CDC/ITSC 2025
│   └── results/             result tables of the papers (CSV)
├── tests/
├── .streamlit/config.toml   Streamlit settings (theme, no usage statistics)
└── requirements.txt
```

## The model in two lines

Each street segment has a **degree of separation (DoS)** from 1 (unmarked lane shared with cars) to
6 (fully separated bike lane). Cyclists choose the path minimising the **cyclist distance**
b = Σ d·s·f^ρ (length × slope factor × traffic factor^ρ, ρ = 0.04); the papers then decide which
segments to upgrade within a budget, to minimise exposure to traffic (ECC), improve the worst-off
cyclists (CDC), or balance cyclists and car travel time (ITSC).

## Deploying (optional)

* Streamlit: [Streamlit Community Cloud](https://streamlit.io/cloud) → *New app* → this repository,
  main file `streamlit_app/app.py`.
* Gradio: [Hugging Face Spaces](https://huggingface.co/spaces) (Gradio SDK) with `gradio_app/app.py`.
