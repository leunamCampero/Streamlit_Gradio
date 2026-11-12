import plotly.express as px
import streamlit as st

from ui import result

st.title("ITSC 2026 - Comparing cities via safety-aware clustering")
st.markdown(
    "Lyon (11,857 nodes) and Strasbourg (11,417) are clustered down to the size of Grenoble "
    "(6,773 nodes) with the proposed **CC-Algorithm** (keeps every cluster DoS-homogeneous and "
    "connected) and with plain spectral **k-means**. The clustered networks are then compared with "
    "Grenoble through a **Gromov-Wasserstein (GW)** distance between exposure measures."
)

sw = result("itsc2026_sweep")
city = st.radio("City", ["Lyon", "Strasbourg"], horizontal=True)
metric = st.radio("Distortion", ["dE_pct", "dPhi_pct", "mixed_arcs_pct", "disconnected_clusters"],
                  horizontal=True,
                  format_func={"dE_pct": "exposure change (%)", "dPhi_pct": "flow change (%)",
                               "mixed_arcs_pct": "arcs in mixed-DoS objects (%)",
                               "disconnected_clusters": "disconnected clusters"}.get)
fig = px.line(sw[sw.city == city], x="k", y=metric, color="method", markers=True,
              color_discrete_map={"CC": "#1b7837", "kmeans": "#b2182b"},
              title=f"{city}: distortion vs number of clusters k (lower is better)")
fig.add_hline(y=0, line_dash="dot")
fig.update_layout(height=420, xaxis_autorange="reversed")
st.plotly_chart(fig, width="stretch")

st.subheader("Which city is closer to Grenoble?")
cmp = result("itsc2026_comparison")
cmp = cmp[(cmp.source == "Grenoble") & cmp.method.isin(["CC", "kmeans"])]
cmp["M (nodes compared)"] = cmp["M"].astype(str)
fig = px.bar(cmp, x="M (nodes compared)", y="GW", color="target", barmode="group",
             facet_col="method", text_auto=".3f", title="GW distance to Grenoble (lower = more similar)")
fig.update_layout(height=420)
st.plotly_chart(fig, width="stretch")
st.success("With CC, **Strasbourg is closer to Grenoble than Lyon** for every M (consistent with the "
           "Baromètre Vélo ranking). With k-means the ranking flips: a comparison is only trustworthy "
           "if the clustering preserves the exposure structure.")
