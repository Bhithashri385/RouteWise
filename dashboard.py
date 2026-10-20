
import json
import sqlite3

import pandas as pd
import streamlit as st

from metrics_db import DB_PATH


st.set_page_config(
    page_title="RouteWise Metrics",
    layout="wide",
)

st.title("RouteWise — Gateway Metrics")
st.caption("Request monitoring | Prompts and answers are not stored")

if st.button("Refresh"):
    st.rerun()

with sqlite3.connect(DB_PATH, timeout=5) as connection:
    rows = pd.read_sql_query(
        """
        SELECT *
        FROM requests
        ORDER BY timestamp_utc DESC
        """,
        connection,
    )

if rows.empty:
    st.info("No requests recorded yet. Send a request through the gateway, then click Refresh.")
    st.stop()

metadata = pd.json_normalize(
    rows["metadata_json"].map(json.loads).tolist()
)

data = pd.concat(
    [rows.drop(columns=["metadata_json"]), metadata],
    axis=1,
)

for column in [
    "backend",
    "requested_model",
    "task",
    "reason",
]:
    if column not in data.columns:
        data[column] = None

for column in ["input_tokens", "output_tokens"]:
    if column not in data.columns:
        data[column] = None

if "attempts" not in data.columns:
    data["attempts"] = [[] for _ in range(len(data))]

if "fallback_used" not in data.columns:
    data["fallback_used"] = False

data["attempts"] = data["attempts"].apply(
    lambda value: value if isinstance(value, list) else []
)
data["fallback_used"] = data["fallback_used"].fillna(False).astype(bool)

data["successful"] = data["status_code"].between(200, 299)
data["failed"] = ~data["successful"]

total = len(data)
successes = int(data["successful"].sum())
failures = int(data["failed"].sum())
fallbacks = int(data["fallback_used"].sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total requests", total)
col2.metric("Successful requests", successes)
col3.metric("Failed requests", failures)
col4.metric("Fallback requests", fallbacks)

st.subheader("Response times")

latency_col1, latency_col2, latency_col3 = st.columns(3)
latency_col1.metric(
    "Average",
    f"{data['latency_ms'].mean():.2f} ms",
)
latency_col2.metric(
    "Median",
    f"{data['latency_ms'].median():.2f} ms",
)
latency_col3.metric(
    "95th percentile",
    f"{data['latency_ms'].quantile(0.95):.2f} ms",
)

st.subheader("Successful requests by model")

successful = data[data["successful"] & data["backend"].notna()]

if successful.empty:
    st.info("No successful model responses recorded yet.")
else:
    model_counts = (
        successful.groupby("backend")
        .size()
        .rename("Successful requests")
        .reset_index()
    )
    st.bar_chart(
        model_counts,
        x="backend",
        y="Successful requests",
    )
    st.dataframe(model_counts, hide_index=True)

st.subheader("Token usage")

token_col1, token_col2 = st.columns(2)

input_tokens = pd.to_numeric(data["input_tokens"], errors="coerce")
output_tokens = pd.to_numeric(data["output_tokens"], errors="coerce")

token_col1.metric(
    "Reported input tokens",
    f"{int(input_tokens.sum())}" if input_tokens.notna().any() else "Unknown",
)
token_col2.metric(
    "Reported output tokens",
    f"{int(output_tokens.sum())}" if output_tokens.notna().any() else "Unknown",
)

st.caption(
    "Token totals include reported usage from successful responses only."
)

st.subheader("Recent requests")

display_columns = [
    "timestamp_utc",
    "request_id",
    "status_code",
    "latency_ms",
    "requested_model",
    "task",
    "backend",
    "attempts",
    "fallback_used",
    "input_tokens",
    "output_tokens",
]

st.dataframe(
    data[display_columns].head(100),
    use_container_width=True,
    hide_index=True,
)
