import plotly.express as px
import streamlit as st

from ui import result

st.title("CDC 2025 - Bike network design and principles of justice")
st.markdown(
    "**Utilitarian** planning (GA-U) minimises the total exposure J_E. **Sufficientarian** planning "
    "(GA-S) makes as many cyclists as possible reach a *sufficient* safety level: a path is "
    "insufficient when its safety is below **lambda x** today's average, and **J_I** measures how far "
    "below the threshold cyclists are. Budget: 5.7 % of B_max (EUR 7.2 M)."
)

s = result("cdc2025_summary")
lam = st.select_slider("Sufficiency threshold lambda (% of today's average safety)",
                       options=[10, 20, 30, 40, 50], value=40)
rows = s[s.solution.isin(["Original", "MLCC", "GA-U", f"GA-S {lam}%"])].copy()
rows["solution"] = rows["solution"].str.replace(f" {lam}%", "")

c1, c2, c3 = st.columns(3)
for col, metric, title in ((c1, f"J_I {lam}%", "Safety insufficiency J_I"),
                           (c2, f"% below {lam}%", "% of cyclists below threshold"),
                           (c3, "J_E", "Total exposure J_E")):
    fig = px.bar(rows, x="solution", y=metric, color="solution", title=title, text_auto=".3g",
                 color_discrete_sequence=["#9e9e9e", "#7b8fc7", "#f4a261", "#1b7837"])
    fig.update_layout(showlegend=False, height=360, yaxis_title=None, xaxis_title=None)
    col.plotly_chart(fig, width="stretch")

ga_u, ga_s = rows.set_index("solution").loc[["GA-U", "GA-S"], f"J_I {lam}%"]
st.success(f"At lambda = {lam} %, GA-S reduces the insufficiency by **{1 - ga_s / ga_u:.0%}** "
           f"compared with GA-U, while its exposure J_E changes by "
           f"{rows.set_index('solution').loc['GA-S', 'J_E'] / rows.set_index('solution').loc['GA-U', 'J_E'] - 1:+.0%}.")

st.subheader("Budget sensitivity (50 GA-S runs)")
b = result("cdc2025_budget_sensitivity")
b["lambda"] = (b["lam"] * 100).astype(int).astype(str) + " %"
b["budget (% of B_max)"] = b["beta"] * 100
y = st.radio("Quantity", ["objective", "J_I", "J_E", "below"], horizontal=True,
             format_func={"objective": "J_I + eta J_E", "J_I": "J_I", "J_E": "J_E",
                          "below": "share below threshold"}.get)
fig = px.line(b, x="budget (% of B_max)", y=y, color="lambda", markers=True, log_x=True)
fig.update_layout(height=420)
st.plotly_chart(fig, width="stretch")
st.caption("Returns diminish quickly: above ~14 % of B_max extra money barely changes the objective.")
