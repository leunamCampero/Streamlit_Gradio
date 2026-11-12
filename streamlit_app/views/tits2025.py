import numpy as np
import plotly.express as px
import streamlit as st

from ui import result

st.title("T-ITS 2025 - Topology and perceived safety of 14 French cities")
st.markdown(
    "Three graph metrics are computed for each cycling network: node strength **s_G**, closeness "
    "**c_G** and the weighted **largest connected component l_G**. They are compared with the "
    "perceived safety and comfort of the *Baromètre Vélo* survey. Only **l_G** is significant; "
    "the NNLS model is **safety = 0.41 + 0.58 l_G**, **comfort = 0.45 + 0.57 l_G**."
)

metrics = result("tits2025_metrics_cities")
survey = result("tits2025_survey")
df = metrics.merge(survey, on="city")

c1, c2 = st.columns([1, 2])
x = c1.radio("Metric (x axis)", ["l_G", "s_G", "c_G"], help="l_G is the one used in the model")
y = c1.radio("Survey score (y axis)", ["y_safety", "y_comfort"],
             format_func={"y_safety": "safety", "y_comfort": "comfort"}.get)
fig = px.scatter(df, x=x, y=y, text="city", color="split", size="length_m", size_max=30,
                 hover_data={"V": True, "E": True, "length_m": ":.0f"})
if x == "l_G":
    xs = np.linspace(0, df[x].max() * 1.1, 20)
    a, b = (0.41, 0.58) if y == "y_safety" else (0.45, 0.57)
    fig.add_scatter(x=xs, y=a + b * xs, mode="lines", name="model (Eq. 10)", line=dict(dash="dash"))
fig.update_traces(textposition="top center", selector=dict(mode="markers+text"))
fig.update_layout(height=480)
c2.plotly_chart(fig, width="stretch")
r = np.corrcoef(df[x], df[y])[0, 1]
c1.metric("Correlation", f"{r:.2f}")

st.subheader("What if a city grew its connected safe network?")
city = st.selectbox("City", df["city"], index=int(np.flatnonzero(df["city"] == "Grenoble")[0]))
row = df[df.city == city].iloc[0]
new_l = st.slider("l_G after upgrades", 0.0, 1.0, float(round(row.l_G, 3)), 0.01)
c1, c2 = st.columns(2)
c1.metric("Predicted safety", f"{0.41 + 0.58 * new_l:.3f}", f"{0.58 * (new_l - row.l_G):+.3f}")
c2.metric("Predicted comfort", f"{0.45 + 0.57 * new_l:.3f}", f"{0.57 * (new_l - row.l_G):+.3f}")
st.caption(f"Full upgrade of {city} to DoS 6 would cost EUR {row.B_max_eur / 1e6:,.0f} M.")

st.dataframe(df, hide_index=True, width="stretch")
