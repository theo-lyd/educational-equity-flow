"""Dashboard drill-down module for district-level exploration."""

from __future__ import annotations

from pathlib import Path

import altair as alt
import duckdb
import pandas as pd

DEFAULT_DB_PATH = Path("warehouse") / "analytics.duckdb"


def _connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path), read_only=True)


def get_district_list(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Load list of all districts with basic metrics."""
    con = _connect(db_path)
    df = con.execute(
        """
        select
            ags,
            region,
            end_to_end_completion_rate,
            compounded_transition_rate
        from gold_transition_rates
        order by region, ags
        """
    ).fetchdf()
    con.close()
    return df


def get_district_pipeline(ags: str, db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Get detailed stage-to-stage pipeline for a single district."""
    con = _connect(db_path)
    df = con.execute(
        f"""
        select
            ags,
            region,
            stage_1_students,
            stage_2_students,
            stage_3_graduates,
            stage_4_university_students,
            stage_5_degree_completions,
            round(
                (stage_2_students / nullif(stage_1_students, 0))::numeric, 4
            ) as transition_1_to_2,
            round(
                (stage_3_graduates / nullif(stage_2_students, 0))::numeric, 4
            ) as transition_2_to_3,
            round(
                (
                    stage_4_university_students
                    / nullif(stage_3_graduates, 0)
                )::numeric,
                4
            ) as transition_3_to_4,
            round(
                (
                    stage_5_degree_completions
                    / nullif(stage_4_university_students, 0)
                )::numeric,
                4
            ) as transition_4_to_5,
            round(
                (stage_5_degree_completions / nullif(stage_1_students, 0))::numeric, 4
            ) as end_to_end_rate
        from gold_stage_funnel
        where ags = '{ags}'
        """
    ).fetchdf()
    con.close()
    return df


def get_district_leakage_timeseries(
    ags: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Get historical leakage differential trend for a district."""
    con = _connect(db_path)
    df = con.execute(
        f"""
        select
            year,
            leakage_differential,
            international_share,
            round(
                leakage_differential * 100.0,
                2
            ) as leakage_pct
        from gold_leakage_differential
        where ags = '{ags}'
        order by year
        """
    ).fetchdf()
    con.close()
    return df


def get_district_subject_breakdown(
    ags: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Get subject and demographic breakdown for a district."""
    con = _connect(db_path)
    df = con.execute(
        f"""
        select
            hs_fg2_group,
            demographic_group,
            subject_completion_share,
            passed_exams,
            total_passed_exams,
            round(
                (passed_exams / nullif(total_passed_exams, 0))::numeric,
                4
            ) as pass_rate
        from gold_subject_resilience
        where ags = '{ags}'
        order by hs_fg2_group, demographic_group
        """
    ).fetchdf()
    con.close()
    return df


def get_district_cluster_peer_group(
    ags: str,
    artifact_dir: Path = Path("warehouse") / "artifacts",
) -> tuple[int | None, pd.DataFrame]:
    """Get cluster assignment and peer group for a district."""
    cluster_path = artifact_dir / "phase07_cluster_assignments.csv"

    if not cluster_path.exists():
        return None, pd.DataFrame()

    cluster_df = pd.read_csv(cluster_path)
    if cluster_df.empty or ags not in cluster_df["ags"].values:
        return None, pd.DataFrame()

    district_record = cluster_df[cluster_df["ags"] == ags].iloc[0]
    cluster_id = int(district_record["cluster_id"])

    peer_group = cluster_df[cluster_df["cluster_id"] == cluster_id].copy()
    peer_group = peer_group.sort_values("ags")

    return cluster_id, peer_group


def get_region_comparison(
    region: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Get all districts in a region for comparison."""
    con = _connect(db_path)
    df = con.execute(
        f"""
        select
            ags,
            region,
            end_to_end_completion_rate,
            compounded_transition_rate,
            transition_rate_1_to_2,
            transition_rate_2_to_3,
            transition_rate_3_to_4,
            transition_rate_4_to_5
        from gold_transition_rates
        where region = '{region}'
        order by end_to_end_completion_rate desc
        """
    ).fetchdf()
    con.close()
    return df


def get_cluster_summary(
    artifact_dir: Path = Path("warehouse") / "artifacts",
) -> pd.DataFrame:
    """Load cluster summary with district counts."""
    summary_path = artifact_dir / "phase07_cluster_summary.csv"

    if not summary_path.exists():
        return pd.DataFrame()

    return pd.read_csv(summary_path)


def build_pipeline_chart(pipeline_df: pd.DataFrame) -> alt.Chart:
    """Create bar chart showing stage pipeline with dropoff."""
    if pipeline_df.empty:
        return alt.Chart(pd.DataFrame()).mark_bar()

    row = pipeline_df.iloc[0]

    data = pd.DataFrame(
        {
            "stage": [
                "Stage 1\n(Grade 7)",
                "Stage 2\n(Grade 11)",
                "Stage 3\n(Graduation)",
                "Stage 4\n(University)",
                "Stage 5\n(Completion)",
            ],
            "students": [
                row["stage_1_students"],
                row["stage_2_students"],
                row["stage_3_graduates"],
                row["stage_4_university_students"],
                row["stage_5_degree_completions"],
            ],
        }
    )

    return (
        alt.Chart(data)
        .mark_bar(color="#0f4c5c", cornerRadius=4)
        .encode(
            x=alt.X("stage:N", title="Educational Stage", sort=None),
            y=alt.Y("students:Q", title="Student Count"),
            tooltip=["stage", alt.Tooltip("students:Q", format=",.0f")],
        )
        .properties(height=300, width=600)
    )


def build_transition_rates_chart(pipeline_df: pd.DataFrame) -> alt.Chart:
    """Create line chart showing transition rates."""
    if pipeline_df.empty:
        return alt.Chart(pd.DataFrame()).mark_line()

    row = pipeline_df.iloc[0]

    data = pd.DataFrame(
        {
            "transition": [
                "1→2",
                "2→3",
                "3→4",
                "4→5",
            ],
            "rate": [
                row["transition_1_to_2"] * 100,
                row["transition_2_to_3"] * 100,
                row["transition_3_to_4"] * 100,
                row["transition_4_to_5"] * 100,
            ],
        }
    )

    return (
        alt.Chart(data)
        .mark_line(point=True, color="#d97706", size=3)
        .encode(
            x=alt.X("transition:N", title="Transition Path", sort=None),
            y=alt.Y("rate:Q", title="Success Rate (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=["transition", alt.Tooltip("rate:Q", format=".1f")],
        )
        .properties(height=280, width=600)
    )


def build_leakage_timeseries_chart(leakage_df: pd.DataFrame) -> alt.Chart:
    """Create line chart showing leakage differential over time."""
    if leakage_df.empty:
        return alt.Chart(pd.DataFrame()).mark_line()

    return (
        alt.Chart(leakage_df)
        .mark_line(point=True, color="#b45309", size=2)
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("leakage_pct:Q", title="Leakage Differential (%)"),
            tooltip=["year", alt.Tooltip("leakage_pct:Q", format=".2f")],
        )
        .properties(height=280, width=600)
    )


def build_subject_breakdown_chart(subject_df: pd.DataFrame) -> alt.Chart:
    """Create grouped bar chart for subject and demographic breakdown."""
    if subject_df.empty:
        return alt.Chart(pd.DataFrame()).mark_bar()

    return (
        alt.Chart(subject_df)
        .mark_bar(cornerRadius=3)
        .encode(
            x=alt.X("hs_fg2_group:N", title="Subject Group", sort="-y"),
            y=alt.Y(
                "subject_completion_share:Q",
                title="Completion Share",
                scale=alt.Scale(domain=[0, 1]),
            ),
            color=alt.Color("demographic_group:N", title="Demographic Group"),
            tooltip=[
                "hs_fg2_group",
                "demographic_group",
                alt.Tooltip("subject_completion_share:Q", format=".2%"),
            ],
        )
        .properties(height=300, width=700)
    )


def build_region_comparison_chart(region_df: pd.DataFrame) -> alt.Chart:
    """Create scatter plot comparing districts in a region."""
    if region_df.empty:
        return alt.Chart(pd.DataFrame()).mark_circle()

    return (
        alt.Chart(region_df)
        .mark_circle(opacity=0.7, size=200)
        .encode(
            x=alt.X(
                "transition_rate_1_to_2:Q",
                title="Grade 7→11 Transition Rate",
                scale=alt.Scale(domain=[0, 1]),
            ),
            y=alt.Y(
                "end_to_end_completion_rate:Q",
                title="End-to-End Completion Rate",
                scale=alt.Scale(domain=[0, 1]),
            ),
            color=alt.Color("transition_rate_4_to_5:Q", title="4→5 Transition Rate"),
            tooltip=["ags", "region", alt.Tooltip("end_to_end_completion_rate:Q", format=".2%")],
        )
        .properties(height=400, width=600)
    )
