import plotly.express as px
import streamlit as st

from core.cycling import DOS_COLORS
from ui import network, network_map, result

st.title("ECC 2025 - Upgrading Grenoble by degree of separation")
st.markdown(
    "Bi-level problem: the **lower level** routes 22,199 daily bike trips on the cyclist distance; "
    "the **upper level** upgrades lanes within 50 % of B_max (EUR 63 M) to minimise the cyclists' "
    "exposure to traffic **J_E**. **GAB** (genetic algorithm) uses the flows; **MLCC** grows the "
    "largest connected DoS-6 network and ignores them."
)

t = result("ecc2025_table3")
c1, c2, c3 = st.columns(3)
for col, (_, r) in zip((c1, c2, c3), t.iterrows()):
    col.metric(f"J_E - {r.solution}", f"{r.J_E:.3f}",
               None if r.reduction == 0 else f"-{r.reduction:.1%}", delta_color="inverse")

km = t.melt(id_vars="solution", value_vars=[f"DoS{k} km" for k in range(6, 0, -1)],
            var_name="DoS", value_name="km")
km["DoS"] = km["DoS"].str.replace(" km", "").str.replace("DoS", "DoS ")
fig = px.bar(km, x="solution", y="km", color="DoS", barmode="stack",
             color_discrete_map={f"DoS {k}": c for k, c in DOS_COLORS.items()},
             title="Km of network per DoS (Table III)")
fig.update_layout(height=400)
st.plotly_chart(fig, width="stretch")

st.subheader("Where does each method spend the budget?")
net = network()
c1, c2 = st.columns(2)
for col, key, name in ((c1, "ecc2025_gab", "GAB"), (c2, "ecc2025_mlcc", "MLCC")):
    d = net.dos(key)
    col.markdown(f"**{name}** - upgraded edges only")
    col.plotly_chart(network_map(d, highlight=d != net.dos0, height=450),
                     width="stretch", key=key)

st.info("GAB removes every DoS 1-3 edge on the routes cyclists actually use; MLCC builds more "
        "DoS-6 km (189 vs 127) but leaves 46 km of DoS 1-2 on busy routes. The two methods are "
        "complementary: GAB for exposure, MLCC for connectivity.")
st.dataframe(t, hide_index=True, width="stretch")
