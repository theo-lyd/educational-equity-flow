"""Streamlit app entrypoint for educational-equity-flow."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.drilldown import (
    build_leakage_timeseries_chart,
    build_pipeline_chart,
    build_region_comparison_chart,
    build_subject_breakdown_chart,
    build_transition_rates_chart,
    get_cluster_summary,
    get_district_cluster_peer_group,
    get_district_leakage_timeseries,
    get_district_list,
    get_district_pipeline,
    get_district_subject_breakdown,
    get_region_comparison,
)
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


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>Educational Equity and Talent Leakage Observatory</h1>
                    <p>
                        Phase 10 dashboard for policy interpretation,
                        reproducibility evidence, and defense readiness.
                    </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(funnel_df: pd.DataFrame) -> None:
    top_row = st.columns(4)
    total_stage_1 = int(funnel_df["stage_1_students"].fillna(0).sum()) if not funnel_df.empty else 0
    total_stage_5 = (
        int(funnel_df["stage_5_degree_completions"].fillna(0).sum()) if not funnel_df.empty else 0
    )
    completion_rate = (total_stage_5 / total_stage_1) if total_stage_1 else 0.0

    top_row[0].metric("Districts", f"{len(funnel_df):,}")
    top_row[1].metric("Stage 1 Cohort", f"{total_stage_1:,}")
    top_row[2].metric("Stage 5 Completions", f"{total_stage_5:,}")
    top_row[3].metric("End-to-End Rate", f"{completion_rate:.1%}")


def render_funnel(sankey_df: pd.DataFrame) -> None:
    st.subheader("Leakage Funnel (Sankey-style)")
    if sankey_df.empty:
        st.warning("No stage funnel data is available.")
        return

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


def render_anomaly_map(anomaly_df: pd.DataFrame) -> None:
    st.subheader("District Anomaly Map")
    if anomaly_df.empty:
        st.warning("No anomaly data is available.")
        return

    st.caption(
        "Map uses deterministic AGS-based pseudo-coordinates in CI-safe mode "
        "when official district geometries are not packaged."
    )
    map_chart = (
        alt.Chart(anomaly_df)
        .mark_circle(opacity=0.8)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size(
                "anomaly_score:Q", title="Anomaly Score", scale=alt.Scale(range=[35, 800])
            ),
            color=alt.Color(
                "anomaly_score:Q", title="Anomaly Score", scale=alt.Scale(scheme="orangered")
            ),
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


def render_scd_timeline() -> None:
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
        return

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


def render_subject_resilience(subject_df: pd.DataFrame) -> None:
    st.subheader("Subject-Level Talent Resilience")
    if subject_df.empty:
        st.warning("No subject resilience data is available.")
        return

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


def render_evidence(evidence: dict[str, object]) -> None:
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
1. Data lineage: raw multi-format public sources are contract-profiled,
    normalized, and modeled through Bronze/Silver/Gold.
2. Reliability: dbt tests, quality checks, and CI pipelines
    guard each merge and scheduled freshness review.
3. Intelligence: clustering and forecasts generate policy segmentation and forward planning inputs.
4. Interpretation: dashboard views connect leakage dynamics
    to district-level and subject-level outcomes.
"""
    )


def render_walkthrough(evidence: dict[str, object]) -> None:
    st.subheader("Reviewer Walkthrough Mode")
    st.caption("Use this mode during defense to guide reviewers in a fixed, step-by-step order.")

    steps = st.tabs(
        [
            "Step 1: Context",
            "Step 2: Funnel",
            "Step 3: Geography",
            "Step 4: History",
            "Step 5: Resilience + Evidence",
        ]
    )

    with steps[0]:
        st.markdown(
            """
1. Start with the KPI strip: district count,
   stage-1 cohort size, stage-5 completions,
   and end-to-end completion rate.
2. State the policy question: where and when does educational progression leak most strongly?
3. Clarify scope: district-level observational analytics, not causal claims.
"""
        )

    with steps[1]:
        st.markdown(
            """
1. Show stage transitions from Grade 7 to completion.
2. Use the drop-from-previous line to identify the steepest attrition step.
3. Connect this to potential policy intervention points.
"""
        )

    with steps[2]:
        st.markdown(
            """
1. Open the anomaly map to prioritize districts by risk score.
2. Explain score composition: weak completion + high leakage differential.
3. Use tooltips for district-level detail in Q&A.
"""
        )

    with steps[3]:
        st.markdown(
            """
1. Toggle boundary mode between current and historical.
2. Show that district changes are preserved via snapshot validity columns.
3. Emphasize this protects time-series interpretation under boundary drift.
"""
        )

    with steps[4]:
        st.markdown(
            """
1. Use subject resilience view to highlight heterogeneity by group.
2. Close with reproducibility status and quality report summary.
3. Direct reviewers to
   `docs/phase_10/THESIS_APPENDIX_EVIDENCE.md`
   and `docs/phase_10/DEFENSE_SCRIPT_AND_QA.md`.
"""
        )
        st.write(
            {
                "phase07_report_present": evidence.get("phase07_report_present"),
                "phase08_report_present": evidence.get("phase08_report_present"),
                "phase08_status": evidence.get("phase08_status"),
            }
        )


def render_district_explorer() -> None:
    st.subheader("District Explorer: Interactive Drill-Down")

    # Get district list
    district_list = get_district_list()
    if district_list.empty:
        st.warning("No districts available for exploration.")
        return

    # District selection
    col1, col2 = st.columns(2)
    with col1:
        selected_region = st.selectbox(
            "Select Region",
            options=sorted(district_list["region"].unique()),
            key="drill_region",
        )

    region_districts = district_list[district_list["region"] == selected_region].sort_values("ags")

    with col2:
        def format_district(ags_val: str) -> str:
            """Format district AGS for display."""
            region = region_districts[region_districts["ags"] == ags_val].iloc[0][
                "region"
            ]
            return f"{ags_val} - {region}"

        selected_ags = st.selectbox(
            "Select District (AGS)",
            options=region_districts["ags"].values,
            format_func=format_district,
            key="drill_ags",
        )

    if selected_ags:
        st.markdown("---")

        # Load district data
        pipeline_df = get_district_pipeline(selected_ags)
        leakage_df = get_district_leakage_timeseries(selected_ags)
        subject_df = get_district_subject_breakdown(selected_ags)
        cluster_id, peer_group = get_district_cluster_peer_group(selected_ags)

        if not pipeline_df.empty:
            # Key metrics for this district
            row = pipeline_df.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("End-to-End Rate", f"{row['end_to_end_rate']*100:.1f}%")
            col2.metric("Stage 1 Students", f"{int(row['stage_1_students']):,}")
            col3.metric("Stage 5 Completions", f"{int(row['stage_5_degree_completions']):,}")
            if cluster_id is not None:
                col4.metric("Cluster ID", f"{cluster_id}")

            st.markdown("### Pipeline Progression")
            col1, col2 = st.columns(2)
            with col1:
                st.altair_chart(build_pipeline_chart(pipeline_df), use_container_width=True)
            with col2:
                st.altair_chart(build_transition_rates_chart(pipeline_df), use_container_width=True)

        # Leakage trends
        if not leakage_df.empty:
            st.markdown("### Historical Leakage Trends")
            st.altair_chart(build_leakage_timeseries_chart(leakage_df), use_container_width=True)

        # Subject breakdown
        if not subject_df.empty:
            st.markdown("### Subject and Demographic Breakdown")
            st.altair_chart(build_subject_breakdown_chart(subject_df), use_container_width=True)

        # Peer group
        if not peer_group.empty:
            st.markdown("### Cluster Peer Group")
            peer_display = peer_group[["ags", "region", "cluster_label"]].copy()
            peer_display.columns = ["AGS", "Region", "Cluster Label"]
            st.dataframe(peer_display, use_container_width=True, hide_index=True)


def render_region_comparison() -> None:
    st.subheader("Regional Comparison: District Performance")

    district_list = get_district_list()
    if district_list.empty:
        st.warning("No districts available.")
        return

    selected_region = st.selectbox(
        "Select Region to Compare",
        options=sorted(district_list["region"].unique()),
        key="region_comp",
    )

    region_df = get_region_comparison(selected_region)
    if region_df.empty:
        st.warning(f"No data for region: {selected_region}")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"Districts in {selected_region}", len(region_df))
        avg_rate = region_df["end_to_end_completion_rate"].mean() * 100
        st.metric("Avg End-to-End Rate", f"{avg_rate:.1f}%")

    with col2:
        st.metric("Best Rate", f"{region_df['end_to_end_completion_rate'].max()*100:.1f}%")
        st.metric("Worst Rate", f"{region_df['end_to_end_completion_rate'].min()*100:.1f}%")

    st.markdown("### Scatter: Transition 1→2 vs End-to-End Rate")
    st.altair_chart(build_region_comparison_chart(region_df), use_container_width=True)

    st.markdown("### District Rankings in Region")
    display_df = region_df[["ags", "end_to_end_completion_rate", "transition_rate_1_to_2"]].copy()
    display_df.columns = ["AGS", "End-to-End Rate", "Grade 7→11 Rate"]
    display_df = display_df.sort_values("End-to-End Rate", ascending=False).reset_index(drop=True)
    display_df["End-to-End Rate"] = display_df["End-to-End Rate"].apply(lambda x: f"{x*100:.1f}%")
    display_df["Grade 7→11 Rate"] = display_df["Grade 7→11 Rate"].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_cluster_analysis() -> None:
    st.subheader("Cluster Segmentation Analysis")

    cluster_summary = get_cluster_summary()
    if cluster_summary.empty:
        st.warning("No cluster summary available.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Clusters", len(cluster_summary))
    col2.metric("Total Districts Segmented", int(cluster_summary["district_count"].sum()))
    col3.metric("Avg District Count per Cluster", f"{cluster_summary['district_count'].mean():.1f}")

    st.markdown("### Cluster Profiles")
    display_df = cluster_summary.copy()
    display_df.columns = [
        "Cluster ID",
        "District Count",
        "Avg End-to-End Rate",
        "Avg Transition 4→5",
        "Avg Leakage Diff",
        "Cluster Label",
    ]
    display_df["Avg End-to-End Rate"] = display_df["Avg End-to-End Rate"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
    )
    display_df["Avg Transition 4→5"] = display_df["Avg Transition 4→5"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
    )
    display_df["Avg Leakage Diff"] = display_df["Avg Leakage Diff"].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)


render_header()


funnel_df = load_stage_funnel()
sankey_df = build_sankey_series(funnel_df)
anomaly_df = load_anomaly_map_data()
subject_df = load_subject_resilience()
evidence = load_evidence_metadata()

with st.sidebar:
    st.header("View Mode")
    view_mode = st.radio(
        "Select mode",
        options=[
            "Dashboard Overview",
            "Reviewer Walkthrough",
            "District Explorer",
            "Regional Comparison",
            "Cluster Analysis",
        ],
        help="Drill-down views provide detailed district and regional exploration.",
    )


render_kpis(funnel_df)

if view_mode == "Dashboard Overview":
    render_funnel(sankey_df)
    render_anomaly_map(anomaly_df)
    render_scd_timeline()
    render_subject_resilience(subject_df)
    render_evidence(evidence)
elif view_mode == "Reviewer Walkthrough":
    render_walkthrough(evidence)
elif view_mode == "District Explorer":
    render_district_explorer()
elif view_mode == "Regional Comparison":
    render_region_comparison()
elif view_mode == "Cluster Analysis":
    render_cluster_analysis()
