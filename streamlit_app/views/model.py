import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core.cycling import COST, DOS_COLORS, PSI, RHO, cyclist_distance, dos_table, slope_factor

st.title("Cyclist-distance model")
st.markdown(
    r"""
Cyclists are routed on the **cyclist distance** of each arc (Eq. 1 of ECC 2025):

$$ b_a = d_a \cdot s_a \cdot f_a^{\rho}, \qquad
f_a = \begin{cases}\psi\, e^{AADT_a/1000} & \text{DoS} \le 4\\ 2.03\,\psi & \text{DoS} = 5\\ \psi & \text{DoS}=6\end{cases}$$

$d_a$ = length, $s_a$ = slope factor, $f_a$ = traffic factor, AADT = cars per day next to the lane.
Move the sliders to see how the parameters change the penalties.
"""
)

c1, c2 = st.columns(2)
rho = c1.slider("rho (sensitivity of route choice to traffic)", 0.0, 0.2, RHO, 0.005, format="%.3f")
psi = c2.slider("psi", 0.5, 1.5, PSI, 0.01)

table = dos_table(rho, psi)
st.dataframe(table, hide_index=True, width="stretch")

fig = px.bar(table, x="DoS", y="f^rho (route penalty)", color=table["DoS"].astype(str),
             color_discrete_map={str(k): c for k, c in DOS_COLORS.items()},
             title="How much longer 1 m 'feels' on each DoS")
fig.update_layout(showlegend=False, height=330, xaxis=dict(dtick=1))
st.plotly_chart(fig, width="stretch")

st.subheader("Segment calculator")
c1, c2, c3 = st.columns(3)
length = c1.number_input("Length (m)", 1.0, 10_000.0, 500.0, 10.0)
slope = c2.slider("Slope (%) - negative = downhill", -10.0, 10.0, 0.0, 0.5)
dos = c3.select_slider("DoS", options=[1, 2, 3, 4, 5, 6], value=2)
b = float(cyclist_distance([length], [slope], [dos], rho, psi)[0])
st.metric("Cyclist distance", f"{b:,.0f} m", delta=f"{b / length - 1:+.1%} vs physical length",
          delta_color="inverse")
st.caption(f"Slope factor s_a = {float(slope_factor([slope])[0]):.3f}")

st.subheader("Upgrade cost (Cerema, EUR per metre)")
cost = pd.DataFrame(COST).T.reindex(index=range(1, 7), columns=range(1, 7))
cost.index.name, cost.columns.name = "from DoS", "to DoS"
st.dataframe(cost.style.format(lambda v: "" if np.isnan(v) else f"{v:.0f}"), width="stretch")
c1, c2, c3 = st.columns(3)
frm = c1.selectbox("From DoS", [1, 2, 3, 4, 5], index=1)
to = c2.selectbox("To DoS", [d for d in range(frm + 1, 7)], index=None, placeholder="pick")
km = c3.number_input("Km to upgrade", 0.1, 300.0, 5.0, 0.5)
if to:
    st.metric("Cost", f"EUR {COST[frm][to] * km * 1000 / 1e6:.2f} M")
