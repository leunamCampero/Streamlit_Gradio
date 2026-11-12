"""
Gradio demo: a cyclist route planner on the Grenoble network of the thesis.

    python gradio_app/app.py        -> open http://127.0.0.1:7860

Unlike Streamlit (which re-runs a whole script), Gradio wires *functions* to widgets:
``button.click(fn, inputs=[...], outputs=[...])`` calls ``fn`` with the input values and puts
what it returns into the output components.
"""
import sys
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.cycling import DOS_COLORS, RHO, SOLUTIONS, load_network  # noqa: E402

net = load_network()
zones = net.zones[net.zones.zone_id.isin(net.nodes.zone_id.unique())].sort_values("name")
ZONE_CHOICES = [(f"{r.name} ({r.zone_id})", int(r.zone_id)) for r in zones.itertuples()]
SOLUTION_CHOICES = [(label, key) for key, (label, _) in SOLUTIONS.items()]


def _map(routes, dos):
    fig = go.Figure()
    lines = net.edge_lines(dos)
    for k in (1, 2, 3, 4, 5, 6):
        lon, lat = lines[k]
        fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines", name=f"DoS {k}",
                                    line=dict(color=DOS_COLORS[k], width=1.5), opacity=0.45,
                                    hoverinfo="skip"))
    for name, r, color in routes:
        lon, lat = net.route_coords(r)
        fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines", name=name,
                                    line=dict(color=color, width=6)))
    first = routes[0][1]
    for idx, label in ((0, "start"), (-1, "end")):
        n = first.nodes[idx]
        fig.add_trace(go.Scattermap(lon=[net.lon[n]], lat=[net.lat[n]], mode="markers+text",
                                    marker=dict(size=14, color="#111"), text=[label],
                                    textposition="top right", showlegend=False))
    lon, lat = net.route_coords(first)
    fig.update_layout(map=dict(style="carto-positron", zoom=13,
                               center=dict(lon=sum(lon) / len(lon), lat=sum(lat) / len(lat))),
                      height=560, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)"))
    return fig


def plan(origin_zone, destination_zone, solution, rho):
    if origin_zone is None or destination_zone is None:
        raise gr.Error("Choose an origin and a destination.")
    if origin_zone == destination_zone:
        raise gr.Error("Origin and destination must be different neighbourhoods.")
    o, d = net.zone_node(origin_zone), net.zone_node(destination_zone)
    safe = net.route(o, d, solution, weight="cyclist", rho=rho)
    short = net.route(o, d, solution, weight="length")
    rows = []
    for name, r in (("Safest (cyclist distance)", safe), ("Shortest (length only)", short)):
        s = r.to_dict()
        rows.append({"route": name, "length (km)": s["length_km"],
                     "km on DoS 5-6 (separated)": round(s["km_per_dos"][5] + s["km_per_dos"][6], 2),
                     "km on DoS 1-3 (exposed)": s["km_exposed_dos_1_3"],
                     "exposure (km-equiv.)": s["exposure_km_equiv"]})
    table = pd.DataFrame(rows)
    detour = safe.length_m / short.length_m - 1
    msg = (f"The safest route is **{detour:+.0%}** longer than the shortest one and rides "
           f"**{table.iloc[1, 3] - table.iloc[0, 3]:.2f} km less** next to car traffic (DoS 1-3).")
    fig = _map([("Safest route", safe, "#1d4ed8"), ("Shortest route", short, "#e11d48")],
               net.dos(solution))
    return fig, table, msg


def compare_networks(origin_zone, destination_zone, rho):
    """Same trip on every network of the papers."""
    if origin_zone is None or destination_zone is None or origin_zone == destination_zone:
        raise gr.Error("Choose two different neighbourhoods.")
    o, d = net.zone_node(origin_zone), net.zone_node(destination_zone)
    rows = []
    for key, (label, _) in SOLUTIONS.items():
        s = net.route(o, d, key, weight="cyclist", rho=rho).to_dict()
        rows.append({"network": label, "length (km)": s["length_km"],
                     "km on DoS 6": s["km_per_dos"][6],
                     "km on DoS 1-3": s["km_exposed_dos_1_3"],
                     "exposure (km-equiv.)": s["exposure_km_equiv"]})
    return pd.DataFrame(rows)


def predict(l_g):
    return {"safety (0-1)": round(0.41 + 0.58 * l_g, 3), "comfort (0-1)": round(0.45 + 0.57 * l_g, 3)}


with gr.Blocks(title="Grenoble safe-route planner") as demo:
    gr.Markdown("# Grenoble cycling: safe-route planner\n"
                "Routes follow the **cyclist distance** of the thesis (length x slope factor x "
                "traffic factor^rho). Pick two IRIS neighbourhoods and a network: today's, or one "
                "optimised in the papers.")
    with gr.Tab("Route planner"):
        with gr.Row():
            # default trip: the railway station (Gare) -> Village Olympique Nord
            origin = gr.Dropdown(ZONE_CHOICES, label="From", value=52)
            dest = gr.Dropdown(ZONE_CHOICES, label="To", value=115)
            solution = gr.Dropdown(SOLUTION_CHOICES, label="Network", value="original")
        rho = gr.Slider(0.0, 0.3, value=RHO, step=0.01, label="rho - how much cyclists avoid traffic",
                        info=f"paper value {RHO}; higher = longer detours to avoid cars")
        go_btn = gr.Button("Plan route", variant="primary")
        msg = gr.Markdown()
        out_map = gr.Plot(label="Routes")
        out_table = gr.Dataframe(label="Route statistics")
        go_btn.click(plan, [origin, dest, solution, rho], [out_map, out_table, msg])
        demo.load(plan, [origin, dest, solution, rho], [out_map, out_table, msg])
    with gr.Tab("Same trip, every network"):
        gr.Markdown("How the optimised networks of each paper change one trip.")
        cmp_btn = gr.Button("Compare networks", variant="primary")
        cmp_table = gr.Dataframe()
        cmp_btn.click(compare_networks, [origin, dest, rho], cmp_table)
    with gr.Tab("Safety predictor (T-ITS 2025)"):
        gr.Markdown("Perceived safety and comfort predicted from the weighted largest connected "
                    "component **l_G** of a city's network (Grenoble today: 0.203, Strasbourg: 0.376).")
        lg = gr.Slider(0, 1, value=0.203, step=0.01, label="l_G")
        pred = gr.JSON(label="Prediction")
        lg.change(predict, lg, pred)
        demo.load(predict, lg, pred)

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
