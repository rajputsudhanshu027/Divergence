"""Development Divergence Explorer: compare a selected country with countries chosen by the user."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from analysis import supf_break_test
from catalog import COUNTRIES, INDICATORS

MAX_YEAR = datetime.now().year


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_indicator(indicator: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Fetch one indicator for the fixed comparison universe from World Bank."""
    codes = ";".join(COUNTRIES.values())
    url = f"https://api.worldbank.org/v2/country/{codes}/indicator/{indicator}"
    response = requests.get(
        url, params={"date": f"{start_year}:{end_year}", "format": "json", "per_page": 20000}, timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return pd.DataFrame(columns=["country", "code", "year", "value"])
    code_names = {code: name for name, code in COUNTRIES.items()}
    rows = [
        {"country": code_names.get(row["countryiso3code"], row["country"]["value"]), "code": row["countryiso3code"],
         "year": int(row["date"]), "value": row["value"]}
        for row in payload[1] if row.get("value") is not None
    ]
    return pd.DataFrame(rows)


def clean_panel(data: pd.DataFrame) -> pd.DataFrame:
    panel = data.dropna(subset=["value"]).copy()
    panel["year"] = panel["year"].astype(int)
    panel["value"] = pd.to_numeric(panel["value"], errors="coerce")
    return panel.dropna(subset=["value"]).sort_values(["country", "year"])


def summarize_comparisons(data: pd.DataFrame, selected: str, comparisons: list[str]) -> tuple[pd.DataFrame, dict]:
    """Summarize a selected country against a user-chosen comparison group."""
    series = data[data["country"].isin([selected, *comparisons])]
    wide = series.pivot_table(index="year", columns="country", values="value", aggfunc="mean").sort_index()
    missing = [country for country in [selected, *comparisons] if country not in wide.columns or wide[country].notna().sum() == 0]
    if missing:
        return pd.DataFrame(), {"missing_countries": missing}
    comparison_values = wide[comparisons]
    comparison_mean = comparison_values.mean(axis=1)
    out = pd.DataFrame({"Selected country": wide[selected], **{country: wide[country] for country in comparisons},
                        "Comparison mean": comparison_mean,
                        "Comparison countries observed": comparison_values.notna().sum(axis=1)})
    out["Gap"] = out["Selected country"] - comparison_mean
    out["Gap (% of comparison mean)"] = 100 * out["Gap"] / comparison_mean.abs().replace(0, pd.NA)
    valid = out["Gap (% of comparison mean)"].dropna()
    changes = out["Gap (% of comparison mean)"].diff()
    return out.reset_index(), {
        "latest_gap": float(valid.iloc[-1]) if len(valid) else float("nan"),
        "largest_change_year": int(changes.abs().idxmax()) if changes.notna().any() else None,
        "first_year": int(valid.index[0]) if len(valid) else None,
        "last_year": int(valid.index[-1]) if len(valid) else None,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def cached_break_test(data: pd.DataFrame) -> dict:
    return supf_break_test(data, minimum_segment=5, bootstrap_replicates=499)


st.set_page_config(page_title="Development Divergence Explorer", page_icon=None, layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Schibsted+Grotesk:wght@400;500;600;700&display=swap');
:root {
  --ink:#141414; --paper:#fff; --canvas:#f5f5f5; --mist:#e9e9e9; --hairline:#d9d9d9;
  --green:#30a81d; --forest:#21935b; --yellow:#fecc33; --ember:#ff8400;
  --font-display:'Schibsted Grotesk',Arial,sans-serif;
  --font-mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
html, body, [class*="st-"] { color:var(--ink); }
.stApp {
  color:var(--ink); font-family:Arial,Helvetica,sans-serif;
  background-color:var(--canvas);
  background-image:linear-gradient(to right,rgba(217,217,217,.62) 1px,transparent 1px),linear-gradient(to bottom,rgba(217,217,217,.62) 1px,transparent 1px);
  background-size:36px 36px;
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background:transparent; }
[data-testid="stHeader"] { height:0; }
.block-container {max-width:1540px; padding:1.5rem clamp(1.25rem,4.4vw,4.5rem) 5rem;}
h1,h2,h3 {color:var(--ink); letter-spacing:-.02em; font-family:var(--font-display);}
h1 {font-size:2.7rem !important; font-weight:500 !important;}
h2 {font-size:1.7rem !important; font-weight:500 !important;}
h3 {font-size:1.3rem !important; font-weight:500 !important;}
p,li {font-family:Arial,Helvetica,sans-serif;}
a {color:var(--ink); text-underline-offset:3px;}
::selection {background:var(--yellow);color:var(--ink);}
:focus-visible {outline:2px solid var(--green) !important;outline-offset:3px;}
[data-testid="stSidebar"] {background:var(--mist);border-right:1px solid var(--hairline);}
.dde-masthead {padding:0 0 1.25rem;margin:0 0 1rem;}
.dde-nav {display:flex;justify-content:space-between;gap:1rem;padding:.55rem 0 .8rem;border-bottom:1px solid var(--ink);font:400 11px/1.2 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;}
.dde-hero {display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,30%);align-items:end;gap:2rem;padding:2.55rem 0 2rem;}
.dde-title {font:500 clamp(4rem,8vw,7rem)/.88 var(--font-display);letter-spacing:-.035em;margin:0;color:var(--ink);}
.dde-deck {max-width:26ch;margin:0 0 .15rem auto;text-align:left;color:var(--ink);font:400 clamp(1.25rem,1.8vw,1.65rem)/1.2 var(--font-display);}
.dde-deck strong {font-weight:600;}
.dde-note {max-width:34rem;margin:.6rem 0 0 auto;text-align:left;font:400 14px/1.5 Arial,Helvetica,sans-serif;color:var(--ink);}
.dde-dateline {display:flex;justify-content:space-between;gap:1rem;font:400 11px/1.3 var(--font-mono);letter-spacing:.08em;color:var(--ink);text-transform:uppercase;padding-top:.7rem;border-top:1px solid var(--hairline);}
.dde-section-label {margin:0 0 .45rem;font:400 11px/1.25 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:#444;}
.dde-control-title {font:500 1.65rem/1.1 var(--font-display);color:var(--ink);margin:0 0 .2rem;letter-spacing:-.025em;}
.dde-control-hint {font:400 14px/1.5 Arial,Helvetica,sans-serif;color:#353535;margin:0 0 .85rem;}
.dde-resultline {display:flex;align-items:baseline;flex-wrap:wrap;gap:.45rem .75rem;margin:.35rem 0 1.4rem;padding:.75rem 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--hairline);font:400 13px/1.45 var(--font-mono);}
.dde-resultline strong {font:500 1.1rem/1.2 var(--font-display);letter-spacing:-.015em;}
.dde-resultline .dde-gap {background:var(--yellow);padding:.08rem .35rem;font-weight:500;}
[class*="st-key-dde-controls"] {background:rgba(255,255,255,.82);border:1px solid var(--hairline);border-radius:12px;padding:1rem 1.1rem .75rem;margin:.5rem 0 1.25rem;}
[class*="st-key-dde-controls"] [data-testid="stHorizontalBlock"] {gap:.8rem;}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label {font:400 12px/1.2 var(--font-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--ink);}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stNumberInput"] [data-baseweb="input"] > div,
[data-testid="stTextInput"] [data-baseweb="input"] > div {background:var(--canvas);border:1px solid var(--hairline);border-radius:160px;color:var(--ink);}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {background:var(--green);border-color:var(--green);}
button[kind="primary"],.stDownloadButton button {background:var(--ink)!important;color:var(--paper)!important;border:1px solid var(--ink)!important;border-radius:8px!important;font:400 12px/1.2 var(--font-mono)!important;letter-spacing:.06em;text-transform:uppercase;padding:.65rem 1.15rem!important;box-shadow:none!important;}
button[kind="primary"]:hover,.stDownloadButton button:hover {background:#303030!important;border-color:#303030!important;color:var(--paper)!important;}
div[data-testid="stAlert"] {background:var(--paper);border:1px solid var(--hairline);border-radius:16px;color:var(--ink);}
div[data-testid="stPlotlyChart"],div[data-testid="stDataFrame"] {background:var(--paper);border:1px solid var(--hairline);border-radius:16px;padding:.4rem .45rem;}
div[data-testid="stExpander"] {background:rgba(255,255,255,.78);border:1px solid var(--hairline);border-radius:16px;}
[data-testid="stMetric"] {padding:.35rem 0;border-top:1px solid var(--hairline);}
[data-testid="stMetricLabel"] {font:400 11px/1.2 var(--font-mono);letter-spacing:.07em;text-transform:uppercase;}
[data-testid="stMetricValue"] {font-family:var(--font-display);letter-spacing:-.03em;}
hr {border-color:var(--hairline);}
@media(max-width:900px){.block-container{padding:1rem 1.2rem 3rem}.dde-hero{gap:1.5rem}.dde-title{font-size:clamp(3.8rem,9vw,6rem)}}
@media(max-width:700px){.dde-nav{font-size:9px;flex-wrap:wrap}.dde-nav span:last-child{margin-left:auto;text-align:right}.dde-hero{grid-template-columns:1fr;gap:1rem;padding:2rem 0 1.5rem}.dde-title{font-size:clamp(3.35rem,14vw,5.2rem);overflow-wrap:anywhere}.dde-deck,.dde-note{text-align:left;margin-left:0;max-width:34ch}.dde-dateline{font-size:9px;flex-wrap:wrap}.block-container{padding:1rem .85rem 2.5rem}}
</style>
<header class="dde-masthead"><div class="dde-nav"><span>DEVELOPMENT DIVERGENCE EXPLORER</span><span>WORLD BANK&nbsp; / &nbsp;COUNTRY COMPARISON</span></div><div class="dde-hero"><h1 class="dde-title">Divergence</h1><div><p class="dde-deck"><strong>See where country paths part.</strong></p><p class="dde-note">Build a comparison from observed outcomes, years, and countries.</p></div></div><div class="dde-dateline"><span>32-COUNTRY SELECTION UNIVERSE</span><span>DESCRIPTIVE COMPARISON&nbsp; / &nbsp;NO CAUSAL CLAIMS</span></div></header>
""", unsafe_allow_html=True)
st.caption("Exploratory analysis · Peer comparisons are descriptive and do not establish causal effects.")

with st.container(key="dde-controls"):
    st.markdown('<div class="dde-control-title">Build your comparison</div><p class="dde-control-hint">Choose an outcome, a focus country, two or three peers, and an observation window.</p>', unsafe_allow_html=True)
    first_controls = st.columns([1.5, 1.1, 2.0, 1.2], vertical_alignment="bottom")
    indicator_name = first_controls[0].selectbox("Outcome indicator", list(INDICATORS))
    selected_country = first_controls[1].selectbox("Country", list(COUNTRIES), index=list(COUNTRIES).index("India"))
    default_comparisons = [country for country in ["Bangladesh", "Vietnam", "Indonesia"] if country != selected_country][:2]
    comparison_countries = first_controls[2].multiselect(
        "Compare with (choose 2–3)", [country for country in COUNTRIES if country != selected_country],
        default=default_comparisons, max_selections=3, key=f"comparison_countries_{selected_country}",
    )
    year_range = first_controls[3].slider("Outcome period", 1980, MAX_YEAR, (2000, min(2022, MAX_YEAR)))
    if len(comparison_countries) not in (2, 3):
        st.info("Choose two or three comparison countries to continue.")
        st.stop()
    st.caption("Source: World Bank Indicators API · Responses are cached in memory for 24 hours.")

indicator = INDICATORS[indicator_name]
outcome_start = int(year_range[0])
outcome_end = int(year_range[1])
source_label = "World Bank Indicators API"
try:
    with st.spinner("Loading country outcome series…"):
        observations = fetch_indicator(indicator, outcome_start, outcome_end)
        if observations.empty:
            raise ValueError("The World Bank API returned no observations for this outcome and period.")
except (requests.RequestException, ValueError, KeyError) as error:
    st.error(f"World Bank Indicators API could not be loaded: {error}")
    st.info("Check your network connection, then try again or select a different outcome period.")
    st.stop()

observations = clean_panel(observations)
observations = observations[observations["year"].between(outcome_start, outcome_end)]
if observations.empty:
    st.error("No observations are available for this selection.")
    st.stop()

trajectory, metrics = summarize_comparisons(observations, selected_country, comparison_countries)
if trajectory.empty:
    missing = ", ".join(metrics.get("missing_countries", comparison_countries))
    st.error(f"No observations for {missing} in this indicator and period. Choose countries with available data or expand the period.")
    st.stop()
break_test = cached_break_test(trajectory)

st.caption(f"**Data:** {source_label} · **Focus country:** {selected_country} · **Selected comparisons:** {', '.join(comparison_countries)}")
st.caption("Monetary series retain the World Bank's constant 2015 US-dollar units for cross-country comparison; values are not converted to INR.")
available = observations.groupby("country")["year"].agg(first="min", last="max", years="nunique").reset_index()
available = available[available["country"].isin([selected_country, *comparison_countries])]
coverage = available.assign(coverage=available.years / (outcome_end - outcome_start + 1) * 100).sort_values("coverage")
with st.expander("Coverage and data quality", expanded=False):
    st.write("Outcome coverage for the focus and comparison countries")
    st.dataframe(coverage.rename(columns={"country": "Country", "first": "First year", "last": "Last year", "years": "Observed years", "coverage": "Period coverage (%)"}).round(1), hide_index=True, width="stretch")

if trajectory["Gap (% of comparison mean)"].notna().sum() == 0:
    st.error("The selected countries have no overlapping observations in this period. Expand the period or select countries with overlapping data.")
    st.stop()

st.markdown(
    f'<div class="dde-resultline"><strong>{indicator_name}</strong>'
    f'<span>{selected_country} against {len(comparison_countries)} selected countries</span>'
    f'<span class="dde-gap">Latest relative gap {metrics["latest_gap"]:+.1f}%</span>'
    f'<span>Observed {metrics["first_year"]}–{metrics["last_year"]}</span></div>',
    unsafe_allow_html=True,
)

st.subheader(f"{selected_country} and selected countries")
st.caption(f"Each country is shown separately; the comparison mean averages selected-country values available in each year. Values are shown in {indicator_name.lower()}.")
series_columns = ["Selected country", *comparison_countries, "Comparison mean"]
long_data = trajectory.melt(id_vars="year", value_vars=series_columns, var_name="Series", value_name=indicator_name)
long_data["Series"] = long_data["Series"].replace({"Selected country": selected_country})
colors = {selected_country: "#30a81d", "Comparison mean": "#141414"}
colors.update({country: color for country, color in zip(comparison_countries, ["#ff8400", "#21935b", "#fecc33"])})
fig = px.line(long_data, x="year", y=indicator_name, color="Series", line_dash="Series",
              color_discrete_map=colors,
              line_dash_map={"Comparison mean": "dash"})
fig.update_layout(legend_title_text="", margin=dict(l=8, r=8, t=10, b=8), height=440, hovermode="x unified", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", font=dict(color="#141414", family="Arial"), xaxis=dict(gridcolor="#eeeeee", zerolinecolor="#d9d9d9", title=""), yaxis=dict(gridcolor="#eeeeee", zerolinecolor="#d9d9d9", title=indicator_name))
fig.update_traces(line_width=2.2)
st.plotly_chart(fig, width="stretch")

gap_col, countries_col = st.columns([.85, 1.15], gap="large")
with gap_col:
    st.subheader("Separation from selected-country mean")
    st.caption(f"Above zero means {selected_country} is higher on this measure.")
    gap_fig = px.area(trajectory, x="year", y="Gap (% of comparison mean)", color_discrete_sequence=["#30a81d"])
    gap_fig.add_hline(y=0, line_color="#141414", line_width=1)
    if break_test["year"] is not None:
        gap_fig.add_vline(x=break_test["year"], line_dash="dash", line_color="#ff8400")
    gap_fig.update_layout(yaxis_title="Gap from selected-country mean (%)", margin=dict(l=8, r=8, t=10, b=8), height=330, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", font=dict(color="#141414", family="Arial"), xaxis=dict(gridcolor="#e9e9e9", zerolinecolor="#d9d9d9"), yaxis=dict(gridcolor="#e9e9e9", zerolinecolor="#d9d9d9"))
    gap_fig.update_traces(fillcolor="rgba(48,168,29,.16)", line_color="#30a81d")
    st.plotly_chart(gap_fig, width="stretch")
with countries_col:
    st.subheader("Your comparison set")
    st.caption("The comparison mean uses whichever selected countries have an observation in each year.")
    st.dataframe(available.rename(columns={"country": "Country", "first": "First year", "last": "Last year", "years": "Observed years"}), hide_index=True, width="stretch")

with st.expander("Statistical interpretation and sensitivity"):
    st.markdown(
        f"""**Comparison.** The chart shows {selected_country} and each country you selected. The comparison mean is an equal-weight average of available selected-country observations for each year; years with fewer available countries are identified in the downloaded table. It is a descriptive reference, not a matched control group.

**Gap.** The relative gap is `(focus value − selected-country mean) / |selected-country mean| × 100`. The change in gap is the end-to-start difference in percentage points (**{metrics['first_year']}–{metrics['last_year']}**). It describes observed separation; it is not a causal effect or forecast.

**Change-point test.** A single unknown break is tested by the maximum Chow F statistic over candidate dates, comparing one linear trend with two separately fitted trends. The bootstrap null uses an estimated AR(1) residual process and resampled empirical innovations; taking the maximum statistic in every replicate adjusts the p-value for searching across dates. The test is conditional on your selected countries and relative-gap construction. Its p-value is approximate and depends on the AR(1)/innovation assumptions; it is descriptive evidence against one linear trend, not a causal claim."""
    )
    st.write(f"Largest absolute one-year movement in the relative gap: **{metrics['largest_change_year'] or 'unavailable'}**. This is a visual inspection aid only.")
    if break_test["p_value"] is not None:
        st.write(f"Bootstrap sup-F test selects **{break_test['year']}** as the first year after the candidate break (sup-F {break_test['sup_f']:.2f}; empirical p = {break_test['p_value']:.3f}; 95% bootstrap critical value {break_test['critical_95']:.2f}; B = {break_test['replicates']}; estimated AR(1) ρ = {break_test['rho']:.2f}).")
    else:
        st.write(f"Bootstrap sup-F test unavailable: {break_test['reason']} Observed years: {break_test['observations']}.")
st.caption("The test requires at least 12 observed gap values overall, with five or more on each side of a candidate break. It uses 499 bootstrap replicates (minimum attainable p = 0.002). Break-date uncertainty is not summarized as a confidence interval.")

with st.expander("Country case-study prompts"):
    st.write("Three sourced starting points are documented in `CASE_STUDIES.md` (Bangladesh and Ethiopia electricity access; Viet Nam GDP and poverty context). Choose those or any other countries in the comparison selector. The chart alone cannot establish why divergence occurred.")
    st.write("The app does not generate case narratives: outcome indicators do not identify policy mechanisms or validate causal explanations.")

st.subheader("Download data")
export = trajectory.copy()
export["data_source"] = source_label
st.download_button("Download selected-country comparison (CSV)", export.to_csv(index=False).encode("utf-8"),
                   file_name=f"development-divergence-{indicator.lower().replace('.', '-').replace(' ', '-')}.csv", mime="text/csv")
st.caption("World Bank observations can be revised and have uneven coverage. This analysis describes this fixed 32-country universe and is not representative of all countries.")
