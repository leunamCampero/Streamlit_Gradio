"""Helpers shared by the Streamlit pages (cached data + the network map)."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.cycling import DOS_COLORS, DOS_LEVELS, DOS_NAMES, GrenobleNetwork, load_result

GRENOBLE_CENTER = {"lon": 5.724, "lat": 45.183}


@st.cache_resource  # loaded once per server process, shared by all users
def network() -> GrenobleNetwork:
    return GrenobleNetwork()


@st.cache_data  # cached per argument value
def result(name: str):
    return load_result(name)


def network_map(dos, highlight=None, height=600, routes=()) -> go.Figure:
    """Map of the network coloured by DoS.

    highlight: optional boolean mask; edges outside it are drawn thin and grey.
    routes: iterable of (name, lons, lats, color) drawn on top.
    """
    net = network()
    fig = go.Figure()
    if highlight is not None:
        grey = net.edge_lines(np.ones(net.E, int), mask=~highlight)[1]
        fig.add_trace(go.Scattermap(lon=grey[0], lat=grey[1], mode="lines", hoverinfo="skip",
                                    line=dict(color="#c8c8c8", width=1), name="unchanged"))
    lines = net.edge_lines(dos, mask=highlight)
    for k in DOS_LEVELS[::-1]:
        lon, lat = lines[k]
        if lon:
            fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines", hoverinfo="name",
                                        line=dict(color=DOS_COLORS[k], width=3 if k >= 5 else 2),
                                        name=f"DoS {k} - {DOS_NAMES[k]}"))
    for name, lons, lats, color in routes:
        fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode="lines", name=name,
                                    line=dict(color=color, width=6)))
    fig.update_layout(map=dict(style="carto-positron", center=GRENOBLE_CENTER, zoom=12.3),
                      height=height, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                                  bgcolor="rgba(255,255,255,0.85)", font=dict(color="#222")))
    return fig
