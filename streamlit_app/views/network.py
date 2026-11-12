import pandas as pd
import plotly.express as px
import streamlit as st

from core.cycling import DOS_COLORS, SOLUTIONS
from ui import network, network_map

st.title("Grenoble network explorer")
st.caption("Today's network and the optimised networks proposed in the papers, coloured by DoS.")

net = network()
labels = {k: v[0] for k, v in SOLUTIONS.items()}
col_a, col_b = st.columns([2, 1])
solution = col_a.selectbox("Network", list(labels), format_func=labels.get, index=1)
only_changed = col_b.toggle("Show only upgraded edges", value=solution != "original",
                            disabled=solution == "original")

dos = net.dos(solution)
info = net.summary(solution)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Upgrade cost", f"EUR {info['upgrade_cost_eur'] / 1e6:.1f} M")
m2.metric("Share of B_max", f"{info['share_of_B_max']:.1%}")
m3.metric("Edges upgraded", f"{info['edges_upgraded']:,}")
m4.metric("Km of DoS 6", f"{info['km_per_dos'][6]:.0f} km",
          delta=f"{info['km_per_dos'][6] - net.km_per_dos(net.dos0)[6]:+.0f} km vs today")

highlight = (dos != net.dos0) if (only_changed and solution != "original") else None
st.plotly_chart(network_map(dos, highlight=highlight, height=620), width="stretch")

st.subheader("Km per DoS in every network")
rows = [{"network": SOLUTIONS[s][0], "DoS": f"DoS {k}", "km": km}
        for s in SOLUTIONS for k, km in net.km_per_dos(net.dos(s)).items()]
fig = px.bar(pd.DataFrame(rows), y="network", x="km", color="DoS", orientation="h",
             color_discrete_map={f"DoS {k}": c for k, c in DOS_COLORS.items()},
             category_orders={"DoS": [f"DoS {k}" for k in (6, 5, 4, 3, 2, 1)]})
fig.update_layout(height=380, yaxis_title=None, legend_title=None, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, width="stretch")
