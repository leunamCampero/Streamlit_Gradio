import plotly.express as px
import streamlit as st

from ui import network, network_map, result

st.title("ITSC 2025 - Safer bike lanes vs car travel time")
st.markdown(
    "A separated bike lane (DoS >= 5) **halves the capacity** of the car road it runs along. The "
    "upper level minimises **eps x (cyclist exposure) + (1 - eps) x (car total travel time)**. "
    "eps = 1 cares only about cyclists, eps = 0 only about cars."
)

p = result("itsc2025_pareto")
p["budget"] = p["alpha"].map(lambda a: f"{a:.0%} of B_max")
J0, TTT0 = 0.526, 2850.42  # today's exposure and car total travel time (veh.h), from the paper run
p["exposure vs today"] = p["J_E"] / J0
p["car time increase (%)"] = (p["TTT"] / TTT0 - 1) * 100

fig = px.line(p.sort_values("eps"), x="car time increase (%)", y="exposure vs today", color="budget",
              markers=True, hover_data=["eps", "reduced_roads", "reduced_road_km"],
              title="Pareto front (car routes fixed)")
fig.update_layout(height=450)
st.plotly_chart(fig, width="stretch")

st.subheader("After drivers re-route (user equilibrium)")
s = result("itsc2025_summary")
s["budget"] = s["alpha"].map(lambda a: f"{a:.0%} of B_max")
c = st.columns(len(s))
for col, (_, r) in zip(c, s.iterrows()):
    col.markdown(f"**{r.budget}** (eps* = {r.eps_star})")
    col.metric("Exposure", f"-{r.exposure_reduction_pct:.1f} %")
    col.metric("Car time, routes fixed", f"+{r.TTT_fixed_pct:.1f} %")
    col.metric("Car time after re-routing", f"+{r.TTT_UE_pct:.1f} %")
    col.caption(f"{r.reduced_roads} roads narrowed ({r.reduced_road_km:.0f} km)")

st.subheader("The chosen design (1/3 budget, eps* = 0.6)")
net = network()
d = net.dos("itsc2025_eps0.6")
st.plotly_chart(network_map(d, highlight=d != net.dos0, height=520), width="stretch")
st.info("Large safety gains for small car costs: ~90 % less exposure for +1.5 % car travel time "
        "once drivers re-route.")
