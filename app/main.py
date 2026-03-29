"""Streamlit app entrypoint for educational-equity-flow."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.phase10 import (
    build_sankey_series,
    load_anomaly_map_data,
    load_evidence_metadata,
    load_scd_timeline,
    load_stage_funnel,
    load_subject_resilience,
)


st.set_page_config(page_title="Educational Equity Flow", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #0b1220;
        --ocean: #0f4c5c;
        --amber: #d97706;
        --sand: #f7f3ea;
        --leaf: #3a7d44;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.0rem;
        max-width: 1200px;
    }
    .hero {
        background: linear-gradient(120deg, #f8f4e7 0%, #ecf7f8 65%, #f0efe9 100%);
        border: 1px solid #d7dfdf;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .hero h1 {
        color: var(--ink);
        margin: 0;
        font-size: 2.0rem;
        letter-spacing: 0.02em;
    }
    .hero p {
        color: #243447;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }
    .panel {
        background: #ffffff;
        border: 1px solid #dfe6e8;
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        box-shadow: 0 2px 10px rgba(15, 76, 92, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Educational Equity and Talent Leakage Observatory</h1>
      <p>Phase 10 dashboard for policy interpretation, reproducibility evidence, and defense readiness.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

funnel_df = load_stage_funnel()
sankey_df = build_sankey_series(funnel_df)
anomaly_df = load_anomaly_map_data()
subject_df = load_subject_resilience()
evidence = load_evidence_metadata()

top_row = st.columns(4)
total_stage_1 = int(funnel_df["stage_1_students"].fillna(0).sum()) if not funnel_df.empty else 0
total_stage_5 = int(funnel_df["stage_5_degree_completions"].fillna(0).sum()) if not funnel_df.empty else 0
completion_rate = (total_stage_5 / total_stage_1) if total_stage_1 else 0.0

top_row[0].metric("Districts", f"{len(funnel_df):,}")
top_row[1].metric("Stage 1 Cohort", f"{total_stage_1:,}")
top_row[2].metric("Stage 5 Completions", f"{total_stage_5:,}")
top_row[3].metric("End-to-End Rate", f"{completion_rate:.1%}")

st.subheader("Leakage Funnel (Sankey-style)")
if sankey_df.empty:
    st.warning("No stage funnel data is available.")
else:
    funnel_chart = (
        alt.Chart(sankey_df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("source:N", title="Source Stage", sort=None),
            y=alt.Y("value:Q", title="Flow Volume"),
            color=alt.Color(
                "target:N",
                title="Flow Target",
                scale=alt.Scale(
                    domain=[
                        "Stage 2: Grade 11",
                        "Stage 3: Graduation",
                        "Stage 4: University",
                        "Stage 5: Completion",
                    ],
                    range=["#0f4c5c", "#2f7d8c", "#6fa6b3", "#d97706"],
                ),
            ),
            tooltip=["source", "target", alt.Tooltip("value:Q", format=",.0f")],
        )
        .properties(height=320)
    )
    drop_chart = (
        alt.Chart(sankey_df)
        .mark_line(point=True, strokeDash=[7, 4], color="#b45309")
        .encode(
            x=alt.X("source:N", sort=None, title="Source Stage"),
            y=alt.Y("drop_from_previous:Q", title="Drop from Previous Stage"),
            tooltip=["source", alt.Tooltip("drop_from_previous:Q", format=",.0f")],
        )
        .properties(height=180)
    )
    st.altair_chart(funnel_chart, use_container_width=True)
    st.altair_chart(drop_chart, use_container_width=True)

st.subheader("District Anomaly Map")
if anomaly_df.empty:
    st.warning("No anomaly data is available.")
else:
    st.caption(
        "Map uses deterministic AGS-based pseudo-coordinates in CI-safe mode when official district geometries are not packaged."
    )
    map_chart = (
        alt.Chart(anomaly_df)
        .mark_circle(opacity=0.8)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size("anomaly_score:Q", title="Anomaly Score", scale=alt.Scale(range=[35, 800])),
            color=alt.Color("anomaly_score:Q", title="Anomaly Score", scale=alt.Scale(scheme="orangered")),
            tooltip=[
                "ags",
                "region",
                alt.Tooltip("anomaly_score:Q", format=".3f"),
                alt.Tooltip("end_to_end_completion_rate:Q", format=".2%"),
                alt.Tooltip("mean_leakage_differential:Q", format=".3f"),
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(map_chart, use_container_width=True)

st.subheader("SCD Boundary Timeline")
scd_mode = st.radio(
    "Boundary mode",
    options=["current", "historical"],
    horizontal=True,
    help="Switch between current district dimension and snapshot history records.",
)
scd_df = load_scd_timeline(mode=scd_mode)
if scd_df.empty:
    st.info("No SCD records available.")
else:
    if scd_mode == "historical":
        timeline_df = scd_df.copy()
        timeline_df["dbt_valid_from"] = pd.to_datetime(timeline_df["dbt_valid_from"]).dt.date
        timeline_df["dbt_valid_to"] = pd.to_datetime(timeline_df["dbt_valid_to"]).dt.date
        st.dataframe(
            timeline_df[["ags", "region", "latest_year", "dbt_valid_from", "dbt_valid_to"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            scd_df[["ags", "region", "latest_year", "record_type"]],
            use_container_width=True,
            hide_index=True,
        )

st.subheader("Subject-Level Talent Resilience")
if subject_df.empty:
    st.warning("No subject resilience data is available.")
else:
    subject_chart = (
        alt.Chart(subject_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("hs_fg2_group:N", title="Subject Group", sort="-y"),
            y=alt.Y("avg_subject_completion_share:Q", title="Avg Completion Share"),
            color=alt.Color("demographic_group:N", title="Demographic Group"),
            tooltip=[
                "hs_fg2_group",
                "demographic_group",
                alt.Tooltip("avg_subject_completion_share:Q", format=".2%"),
                alt.Tooltip("passed_exams:Q", format=",.0f"),
                alt.Tooltip("total_passed_exams:Q", format=",.0f"),
            ],
        )
        .properties(height=340)
    )
    st.altair_chart(subject_chart, use_container_width=True)

st.subheader("Evidence Appendix and Defense Readiness")
left, right = st.columns(2)
left.markdown("### Reproducibility Evidence")
left.write(
    {
        "phase07_report_present": evidence.get("phase07_report_present"),
        "phase07_cluster_count": evidence.get("phase07_cluster_count"),
        "phase07_forecast_method": evidence.get("phase07_forecast_method"),
        "phase08_report_present": evidence.get("phase08_report_present"),
        "phase08_status": evidence.get("phase08_status"),
        "phase08_fail_count": evidence.get("phase08_fail_count"),
        "phase08_warn_count": evidence.get("phase08_warn_count"),
    }
)

right.markdown("### Defense Narrative")
right.markdown(
    """
1. Data lineage: raw multi-format public sources are contract-profiled, normalized, and modeled through Bronze/Silver/Gold.
2. Reliability: dbt tests, quality checks, and CI pipelines guard each merge and scheduled freshness review.
3. Intelligence: clustering and forecasts generate policy segmentation and forward planning inputs.
4. Interpretation: dashboard views connect leakage dynamics to district-level and subject-level outcomes.
"""
)
