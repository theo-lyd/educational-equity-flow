"""Streamlit app entrypoint for educational-equity-flow."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.cache_utils import clear_dashboard_cache
from src.dashboard.causal_inference import (
    format_confidence_interval,
    run_causal_analysis_pipeline,
    simulate_counterfactual_scenario,
)
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
from src.dashboard.heterogeneity import (
    format_effect_size,
    format_pvalue,
    load_demographic_group_comparison,
    load_subject_heterogeneity_summary,
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

    if "map_source" in anomaly_df.columns:
        source_counts = anomaly_df["map_source"].value_counts().to_dict()
        geojson_count = int(source_counts.get("geojson", 0))
        pseudo_count = int(source_counts.get("pseudo", 0))
        st.caption(
            f"Map coordinates: geojson={geojson_count}, pseudo-fallback={pseudo_count}. "
            "Pseudo values are used when geometry is unavailable."
        )
    else:
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


def render_subject_heterogeneity() -> None:
    st.subheader("Subject Heterogeneity Analysis: Statistical Test Results")
    st.caption(
        "Chi-square tests compare subject completion rates across demographic groups. "
        "Significant p-values (< 0.05) indicate heterogeneous outcomes."
    )

    # Load heterogeneity summary
    hetero_summary = load_subject_heterogeneity_summary()
    if hetero_summary.empty:
        st.warning("No heterogeneity data available.")
        return

    # Display summary table
    st.markdown("### Overall Subject Heterogeneity Results")
    display_summary = hetero_summary[
        [
            "hs_fg2_group",
            "n_demographic_groups",
            "mean_completion",
            "std_completion",
            "chi2_stat",
            "chi2_pvalue",
            "effect_size",
        ]
    ].copy()

    display_summary.columns = [
        "Subject",
        "N Groups",
        "Mean Completion",
        "Std Dev",
        "χ² Statistic",
        "P-value",
        "Cramér's V",
    ]

    # Format columns for display
    display_summary["Mean Completion"] = display_summary["Mean Completion"].apply(
        lambda x: f"{x:.2%}"
    )
    display_summary["Std Dev"] = display_summary["Std Dev"].apply(lambda x: f"{x:.3f}")
    display_summary["χ² Statistic"] = display_summary["χ² Statistic"].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )

    # Use format functions for p-value and effect size
    display_summary["P-value"] = hetero_summary["chi2_pvalue"].apply(format_pvalue)
    display_summary["Cramér's V"] = hetero_summary["effect_size"].apply(format_effect_size)

    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    # Highlight significant subjects
    significant_subjects = hetero_summary[hetero_summary["is_significant_alpha05"]]
    if not significant_subjects.empty:
        st.markdown("### Subjects with Significant Heterogeneity (p < 0.05)")
        sig_text = ", ".join(
            [f"**{subj}**" for subj in significant_subjects["hs_fg2_group"].values]
        )
        st.markdown(f"These subject groups show statistically significant differences across "
                    f"demographic groups: {sig_text}")
    else:
        st.info(
            "No subjects show statistically significant heterogeneity at α = 0.05. "
            "Completion rates are relatively consistent across demographic groups."
        )

    # Detailed demographic breakdown
    st.markdown("### Detailed Demographic Comparison by Subject")
    selected_subject = st.selectbox(
        "Select a subject to explore demographic breakdown:",
        options=sorted(hetero_summary["hs_fg2_group"].unique()),
        key="hetero_subject",
    )

    if selected_subject:
        demo_comparison = load_demographic_group_comparison(selected_subject)
        if not demo_comparison.empty:
            # Display comparison table
            display_demo = demo_comparison.copy()
            display_demo.columns = [
                "Demographic Group",
                "Completion Rate",
                "Passed Exams",
                "Total Exams",
                "N Districts",
            ]
            display_demo["Completion Rate"] = display_demo["Completion Rate"].apply(
                lambda x: f"{x:.2%}"
            )
            st.dataframe(display_demo, use_container_width=True, hide_index=True)

            # Visualization
            chart = (
                alt.Chart(demo_comparison)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X(
                        "demographic_group:N",
                        title="Demographic Group",
                        sort="-y",
                    ),
                    y=alt.Y("completion_rate:Q", title="Completion Rate"),
                    color=alt.Color(
                        "completion_rate:Q",
                        scale=alt.Scale(scheme="viridis"),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("demographic_group:N", title="Group"),
                        alt.Tooltip("completion_rate:Q", format=".2%", title="Completion Rate"),
                        alt.Tooltip("passed_exams:Q", format=",.0f", title="Passed Exams"),
                        alt.Tooltip("total_exams:Q", format=",.0f", title="Total Exams"),
                        alt.Tooltip("n_districts:Q", title="N Districts"),
                    ],
                )
                .properties(height=340)
            )
            st.altair_chart(chart, use_container_width=True)


def render_causal_analysis() -> None:
    """Render causal inference analysis view with treatment effects."""
    st.subheader("Causal Inference: District Intervention Effects")
    st.caption(
        "⚠️ OBSERVATIONAL ANALYSIS: These estimates are from observational data. "
        "Causal interpretations require strong assumptions (no unmeasured "
        "confounding, positivity). Results show association, not definitive "
        "causation."
    )

    # Run causal analysis pipeline
    with st.spinner("Estimating propensity scores and treatment effects..."):
        causal_results = run_causal_analysis_pipeline(caliper=0.1)

    if not causal_results.get("success", False):
        st.error(f"Causal analysis failed: {causal_results.get('message', 'Unknown error')}")
        return

    # Display ATE results
    st.markdown("### Average Treatment Effect (ATE)")
    ate = causal_results["ate"]
    se = causal_results["standard_error"]
    ci = (causal_results["ci_lower"], causal_results["ci_upper"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ATE (Effect Size)", f"{ate:.4f}")
    col2.metric("95% CI", format_confidence_interval(ci[0], ci[1]))
    col3.metric("Standard Error", f"{se:.4f}")
    col4.metric("P-Value Significant", "Yes" if ci[0] > 0 or ci[1] < 0 else "No")

    # Interpretation
    st.markdown("#### Interpretation")
    if ci[0] > 0:
        st.success(
            f"✅ Significant positive effect: Treatment increases outcomes by {ate:.2%} "
            f"(95% CI: {ci[0]:.2%} to {ci[1]:.2%})"
        )
    elif ci[1] < 0:
        st.error(
            f"❌ Significant negative effect: Treatment decreases outcomes by {-ate:.2%} "
            f"(95% CI: {ci[0]:.2%} to {ci[1]:.2%})"
        )
    else:
        st.warning(
            f"⚠️ No significant effect detected at α=0.05. "
            f"Point estimate: {ate:.4f}, CI crosses zero: "
            f"{format_confidence_interval(ci[0], ci[1])}"
        )

    # Matching quality
    st.markdown("### Matching Quality & Covariate Balance")
    col1, col2, col3 = st.columns(3)
    metrics = causal_results["matching_metrics"]
    col1.metric("Districts (Total)", causal_results["n_total"])
    col2.metric("Treated / Control", 
                f"{causal_results['n_treated']} / {causal_results['n_untreated']}")
    col3.metric("Match Rate", 
                f"{metrics['match_rate']:.1%} ({metrics['n_matched']} pairs)")

    # Propensity score balance
    st.markdown("#### Propensity Score Balance (Before/After Matching)")
    balance_before = causal_results["balance_before"]
    balance_after = causal_results["balance_after"]

    balance_df = pd.DataFrame(
        {
            "Metric": ["Treated PS Mean", "Control PS Mean", "Difference"],
            "Before Matching": [
                f"{balance_before['ps_mean_treated']:.4f}",
                f"{balance_before['ps_mean_untreated']:.4f}",
                f"{balance_before['ps_mean_treated'] - balance_before['ps_mean_untreated']:.4f}",
            ],
            "After Matching": [
                f"{balance_after['ps_mean_treated']:.4f}",
                f"{balance_after['ps_mean_untreated']:.4f}",
                f"{balance_after['ps_mean_treated'] - balance_after['ps_mean_untreated']:.4f}",
            ],
        }
    )
    st.dataframe(balance_df, use_container_width=True, hide_index=True)

    st.caption(
        "✅ Good balance: Treated and control groups have similar propensity "
        "scores after matching. This suggests confounding is reduced."
    )

    # Counterfactual scenarios
    st.markdown("### Counterfactual Policy Scenarios")
    st.caption(
        "Simulate hypothetical intervention effects by adjusting district outcomes "
        "under different policy assumptions."
    )

    base_data = causal_results["ps_data"].merge(
        causal_results["matched_data"][["ags", "outcome"]],
        on="ags",
        how="inner",
    )

    scenario_col1, scenario_col2 = st.columns(2)
    with scenario_col1:
        selected_scenario = st.selectbox(
            "Select policy scenario",
            options=["tutoring_boost", "delayed_entry", "remediation"],
            format_func=lambda x: {
                "tutoring_boost": "📚 10% Tutoring Resource Boost",
                "delayed_entry": "⏰ Delayed University Entry",
                "remediation": "🎯 Subject-Specific Remediation",
            }.get(x, x),
        )

    with scenario_col2:
        effect_size = st.slider(
            "Effect size parameter",
            min_value=0.0,
            max_value=0.3,
            value=0.1,
            step=0.02,
        )

    # Run scenario
    scenario_results = simulate_counterfactual_scenario(
        base_data,
        selected_scenario,
        effect_size,
    )

    if scenario_results:
        st.markdown(f"#### {scenario_results['description']}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Baseline Mean Outcome", f"{scenario_results['baseline_mean']:.2%}")
        col2.metric("Counterfactual Outcome", f"{scenario_results['counterfactual_mean']:.2%}")
        col3.metric("Aggregate Effect", f"{scenario_results['aggregate_effect']:+.4f}")

        # Visualization of scenario effects
        scenario_cols = ["ags", "outcome", "counterfactual_outcome"]
        scenario_data = scenario_results["data"][scenario_cols].copy()
        scenario_data["effect"] = (
            scenario_data["counterfactual_outcome"] - scenario_data["outcome"]
        )

        chart = (
            alt.Chart(scenario_data)
            .mark_bar()
            .encode(
                x=alt.X("effect:Q", title="Individual Effect (Outcome Change)"),
                y=alt.Y(
                    "count():Q",
                    title="Number of Districts",
                ),
                color=alt.Color(
                    "effect:Q",
                    scale=alt.Scale(scheme="redblue"),
                    legend=None,
                ),
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

        st.caption(
            "📊 Distribution of individual effects: Districts benefit differently based on "
            "baseline characteristics. Red = negative effects, Blue = positive effects."
        )


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
            "Subject Heterogeneity",
            "Causal Inference",
        ],
        help="Drill-down views provide detailed district and regional exploration.",
    )

    st.divider()
    st.markdown("### Cache Management")
    st.caption("All data is cached for 1 hour. Clear cache to force immediate refresh.")
    if st.button("🔄 Refresh All Data"):
        clear_dashboard_cache()
        st.rerun()


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
elif view_mode == "Subject Heterogeneity":
    render_subject_heterogeneity()
elif view_mode == "Causal Inference":
    render_causal_analysis()
