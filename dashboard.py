import json
import sqlite3

import pandas as pd
import streamlit as st

from metrics_db import DB_PATH

st.set_page_config(
    page_title="RouteWise | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp {
    background-color: #F5F7FB;
    color: #172033;
}
.block-container {
    max-width: 1450px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #172033;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

header, refresh_col = st.columns([5, 1])
with header:
    st.title("RouteWise")
    st.caption("AI Gateway Monitoring Dashboard")
with refresh_col:
    st.write("")
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()

with sqlite3.connect(DB_PATH, timeout=5) as connection:
    rows = pd.read_sql_query(
        "SELECT * FROM requests ORDER BY timestamp_utc DESC",
        connection,
    )

if rows.empty:
    st.info("No requests recorded yet. Send a request through the gateway, then refresh.")
    st.stop()

metadata = pd.json_normalize(rows["metadata_json"].map(json.loads).tolist())
data = pd.concat(
    [rows.drop(columns=["metadata_json"]), metadata],
    axis=1,
)

defaults = {
    "requested_model": None,
    "task": None,
    "reason": None,
    "backend": None,
    "attempts": None,
    "fallback_used": False,
    "input_tokens": None,
    "output_tokens": None,
}
for column, default in defaults.items():
    if column not in data.columns:
        data[column] = default

data["successful"] = data["status_code"].between(200, 299)
data["fallback_used"] = data["fallback_used"].fillna(False).astype(bool)
data["attempts"] = data["attempts"].apply(
    lambda value: value if isinstance(value, list) else []
)

total = len(data)
success_count = int(data["successful"].sum())
failure_count = total - success_count
fallback_count = int(data["fallback_used"].sum())

st.subheader("Request Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Requests", total)
c2.metric("Successful Requests", success_count)
c3.metric("Failed Requests", failure_count)
c4.metric("Fallback Requests", fallback_count)

st.subheader("Response Times")
l1, l2, l3 = st.columns(3)
l1.metric("Average", f"{data['latency_ms'].mean():,.2f} ms")
l2.metric("Median", f"{data['latency_ms'].median():,.2f} ms")
l3.metric("95th Percentile", f"{data['latency_ms'].quantile(0.95):,.2f} ms")

st.subheader("Successful Requests by Model")
successful = data[data["successful"] & data["backend"].notna()]
if successful.empty:
    st.info("No successful model responses recorded yet.")
else:
    model_counts = (
        successful.groupby("backend")
        .size()
        .rename("Successful Requests")
        .reset_index()
    )
    st.bar_chart(model_counts, x="backend", y="Successful Requests")
    st.dataframe(model_counts, hide_index=True, use_container_width=True)

st.subheader("Token Usage")
input_tokens = pd.to_numeric(data["input_tokens"], errors="coerce")
output_tokens = pd.to_numeric(data["output_tokens"], errors="coerce")
t1, t2 = st.columns(2)
t1.metric(
    "Reported Input Tokens",
    f"{int(input_tokens.sum()):,}" if input_tokens.notna().any() else "Unknown",
)
t2.metric(
    "Reported Output Tokens",
    f"{int(output_tokens.sum()):,}" if output_tokens.notna().any() else "Unknown",
)
st.caption("Token totals include reported usage from successful responses only.")

st.subheader("Recent Requests")
search_col, status_col, model_col = st.columns([2, 1, 1])
with search_col:
    search = st.text_input("Search", placeholder="Request ID or model...")
with status_col:
    status_filter = st.selectbox("Status", ["All", "Success", "Failed"])
with model_col:
    model_options = ["All"] + sorted(
        data["requested_model"].dropna().astype(str).unique().tolist()
    )
    model_filter = st.selectbox("Requested Model", model_options)

filtered = data.copy()

if search:
    mask = (
        filtered["request_id"].astype(str).str.contains(
            search, case=False, na=False
        )
        | filtered["requested_model"].astype(str).str.contains(
            search, case=False, na=False
        )
    )
    filtered = filtered[mask]

if status_filter == "Success":
    filtered = filtered[filtered["successful"]]
elif status_filter == "Failed":
    filtered = filtered[~filtered["successful"]]

if model_filter != "All":
    filtered = filtered[
        filtered["requested_model"].astype(str) == model_filter
    ]

filtered["attempts"] = filtered["attempts"].apply(
    lambda attempts: " → ".join(map(str, attempts)) if attempts else "—"
)
filtered["fallback_used"] = filtered["fallback_used"].map(
    {True: "Yes", False: "No"}
)
filtered["latency_ms"] = filtered["latency_ms"].map(
    lambda value: f"{value:,.2f} ms"
)

display_columns = [
    "timestamp_utc",
    "request_id",
    "requested_model",
    "status_code",
    "latency_ms",
    "backend",
    "attempts",
    "fallback_used",
    "input_tokens",
    "output_tokens",
]

st.dataframe(
    filtered[display_columns].head(100),
    use_container_width=True,
    hide_index=True,
    column_config={
        "timestamp_utc": "Time (UTC)",
        "request_id": "Request ID",
        "requested_model": "Requested Model",
        "status_code": "Status",
        "latency_ms": "Response Time",
        "backend": "Successful Backend",
        "attempts": "Model Attempts",
        "fallback_used": "Fallback",
        "input_tokens": "Input Tokens",
        "output_tokens": "Output Tokens",
    },
)

st.caption(
    "Prompts and answers are not stored in the metrics database. "
    "Unknown token counts remain unknown. The table displays the latest "
    "100 matching requests."
)
