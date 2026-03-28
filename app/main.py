"""Streamlit app entrypoint for educational-equity-flow."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Educational Equity Flow", layout="wide")

st.title("Educational Equity & Talent Leakage")
st.caption("Phase 02 foundation app shell")

st.markdown(
    """
This placeholder app confirms the baseline command interface is wired.

Upcoming phases will add:
- Leakage funnel visuals
- District anomaly and cluster views
- Forecast scenarios for policy planning
"""
)

col1, col2 = st.columns(2)
col1.metric("Pipeline Phase", "02", "Foundation")
col2.metric("Status", "Ready", "Scaffold complete")
