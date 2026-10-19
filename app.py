from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from world_bank import INDICATORS, WorldBankError, fetch_panel


st.set_page_config(page_title="EconViz Lab", page_icon="📈", layout="wide")
st.title("EconViz Lab")
st.caption("Explore macroeconomic indicators from the World Bank. Each measure has its own axis and units.")

with st.sidebar:
    country = st.text_input("Country ISO-3 code", value="FRA", max_chars=3).strip().upper()
    start = st.number_input("Start year", min_value=1960, max_value=datetime.now().year, value=2000)
    end = st.number_input("End year", min_value=1960, max_value=datetime.now().year, value=datetime.now().year - 1)
    st.markdown("**One-year what-if shocks (percentage points)**")
    shocks = {
        "NY.GDP.MKTP.KD.ZG": st.slider("GDP growth shock", -10.0, 10.0, 0.0, 0.5),
        "FP.CPI.TOTL.ZG": st.slider("Inflation shock", -10.0, 10.0, 0.0, 0.5),
        "SL.UEM.TOTL.ZS": st.slider("Unemployment shock", -10.0, 10.0, 0.0, 0.5),
    }
    run = st.button("Load data", type="primary")

if "macro_panel" not in st.session_state:
    st.session_state["macro_panel"] = None
if "macro_query" not in st.session_state:
    st.session_state["macro_query"] = None
if run:
    try:
        with st.spinner("Retrieving World Bank observations…"):
            st.session_state["macro_panel"] = fetch_panel(country, int(start), int(end))
            st.session_state["macro_query"] = (country, int(start), int(end))
    except WorldBankError as exc:
        st.session_state["macro_panel"] = None
        st.session_state["macro_query"] = None
        st.error(str(exc))

panel = st.session_state["macro_panel"]
loaded_country, loaded_start, loaded_end = st.session_state["macro_query"] or (country, int(start), int(end))
if panel is None:
    st.info("Choose a country and year range, then load the official WDI observations.")
    st.stop()

countries = panel["country"].dropna().unique()
if len(countries):
    st.subheader(f"{countries[0]} ({loaded_country})")
stamp = panel["retrieved_at_utc"].dropna().max()
st.caption(f"World Development Indicators · retrieved {stamp} · missing observations remain blank")

# Adapt the multi-series comparison idea into separate small multiples to avoid mixing units.
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.10, subplot_titles=list(INDICATORS.values()))
colors = ["#4467A3", "#AE3030", "#009E73"]
for row, (code, label) in enumerate(INDICATORS.items(), start=1):
    series = panel.loc[panel["indicator_code"] == code].sort_values("year")
    fig.add_trace(go.Scatter(x=series["year"], y=series["value"], name=label, mode="lines+markers", line={"color": colors[row - 1], "width": 2}, connectgaps=False), row=row, col=1)
    observed = series.dropna()
    if not observed.empty:
        latest = observed.iloc[-1]
        scenario_value = float(latest["value"]) + shocks[code]
        fig.add_trace(
            go.Scatter(
                x=[latest["year"], int(latest["year"]) + 1],
                y=[latest["value"], scenario_value],
                mode="lines+markers",
                name="User-defined what-if",
                line={"color": "#BD8233", "width": 2, "dash": "dot"},
                marker={"symbol": ["circle", "diamond"], "size": [7, 10]},
                hovertemplate="Year %{x}<br>Illustrative value %{y:.2f}%<extra>User-defined scenario</extra>",
                showlegend=False,
            ),
            row=row,
            col=1,
        )
    fig.update_yaxes(title_text="Annual %", row=row, col=1, zeroline=True)
fig.update_xaxes(title_text="Year", row=3, col=1)
fig.update_layout(height=780, showlegend=False, template="plotly_white", hovermode="x unified", margin={"t": 80})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Observation table")
st_data = panel.sort_values(["indicator_code", "year"])
st.dataframe(st_data, use_container_width=True, hide_index=True)
csv = st_data.to_csv(index=False).encode("utf-8")
st.download_button("Download data and provenance", csv, file_name=f"wdi_{loaded_country}_{loaded_start}_{loaded_end}.csv", mime="text/csv")
st.caption("Interpret indicators using their WDI source notes. Co-movement in this chart does not establish causation.")
st.warning("The dotted point uses your manually selected shock from the latest non-missing value. It is a what-if illustration, not a forecast, probability estimate, or causal model.")
