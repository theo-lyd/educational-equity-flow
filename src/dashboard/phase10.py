"""Phase 10 dashboard data loaders and transforms."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = Path("warehouse") / "analytics.duckdb"
DEFAULT_ARTIFACT_DIR = Path("warehouse") / "artifacts"
DEFAULT_GEOJSON_PATH = Path("data") / "reference" / "districts.geojson"


def _connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path), read_only=True)


def _fetch_df(
    query: str,
    db_path: Path = DEFAULT_DB_PATH,
    params: Sequence[object] | None = None,
) -> pd.DataFrame:
    with _connect(db_path) as con:
        if params is None:
            return con.execute(query).fetchdf()
        return con.execute(query, params).fetchdf()


def ags_to_lat_lon(ags: str) -> tuple[float, float]:
    """Map AGS to deterministic pseudo-geographic coordinates within Germany-like bounds."""
    digest = hashlib.md5(ags.encode("utf-8")).hexdigest()
    lat_seed = int(digest[:8], 16) / 0xFFFFFFFF
    lon_seed = int(digest[8:16], 16) / 0xFFFFFFFF

    lat = 47.2 + (55.0 - 47.2) * lat_seed
    lon = 5.9 + (15.1 - 5.9) * lon_seed
    return round(lat, 5), round(lon, 5)


def _normalize_ags(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # District identifiers are commonly 5 digits in this pipeline.
    return text.zfill(5)


def _extract_feature_ags(feature: dict[str, object]) -> str | None:
    props_obj = feature.get("properties")
    properties = props_obj if isinstance(props_obj, dict) else {}
    for key in ("ags", "AGS", "district_id", "id", "code"):
        if key in properties:
            return _normalize_ags(properties[key])
    return _normalize_ags(feature.get("id"))


def _collect_points(coords: object) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    if isinstance(coords, list):
        if len(coords) >= 2 and isinstance(coords[0], int | float):
            lon = float(coords[0])
            lat = float(coords[1])
            points.append((lat, lon))
        else:
            for child in coords:
                points.extend(_collect_points(child))

    return points


def _centroid_from_geometry(geometry: dict[str, object]) -> tuple[float, float] | None:
    coords = geometry.get("coordinates")
    points = _collect_points(coords)
    if not points:
        return None

    lat = sum(p[0] for p in points) / len(points)
    lon = sum(p[1] for p in points) / len(points)
    return (round(lat, 5), round(lon, 5))


@st.cache_data(ttl=3600)
def load_geojson_centroids(geojson_path: Path = DEFAULT_GEOJSON_PATH) -> pd.DataFrame:
    if not geojson_path.exists():
        return pd.DataFrame(columns=["ags", "lat", "lon"])

    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = payload.get("features", []) if isinstance(payload, dict) else []

    rows: list[dict[str, object]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue

        ags = _extract_feature_ags(feature)
        geometry_obj = feature.get("geometry")
        geometry = geometry_obj if isinstance(geometry_obj, dict) else None
        centroid = _centroid_from_geometry(geometry) if geometry else None

        if ags is None or centroid is None:
            continue

        rows.append({"ags": ags, "lat": centroid[0], "lon": centroid[1]})

    if not rows:
        return pd.DataFrame(columns=["ags", "lat", "lon"])

    df = pd.DataFrame(rows).drop_duplicates(subset=["ags"], keep="first")
    return df[["ags", "lat", "lon"]]


@st.cache_data(ttl=3600)
def load_stage_funnel(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    return _fetch_df(
        """
        select
            ags,
            region,
            stage_1_students,
            stage_2_students,
            stage_3_graduates,
            stage_4_university_students,
            stage_5_degree_completions
        from gold_stage_funnel
        """,
        db_path=db_path,
    )


def build_sankey_series(stage_funnel: pd.DataFrame) -> pd.DataFrame:
    totals = {
        "Stage 1: Grade 7": float(stage_funnel["stage_1_students"].fillna(0).sum()),
        "Stage 2: Grade 11": float(stage_funnel["stage_2_students"].fillna(0).sum()),
        "Stage 3: Graduation": float(stage_funnel["stage_3_graduates"].fillna(0).sum()),
        "Stage 4: University": float(stage_funnel["stage_4_university_students"].fillna(0).sum()),
        "Stage 5: Completion": float(stage_funnel["stage_5_degree_completions"].fillna(0).sum()),
    }
    return pd.DataFrame(
        {
            "source": [
                "Stage 1: Grade 7",
                "Stage 2: Grade 11",
                "Stage 3: Graduation",
                "Stage 4: University",
            ],
            "target": [
                "Stage 2: Grade 11",
                "Stage 3: Graduation",
                "Stage 4: University",
                "Stage 5: Completion",
            ],
            "value": [
                totals["Stage 2: Grade 11"],
                totals["Stage 3: Graduation"],
                totals["Stage 4: University"],
                totals["Stage 5: Completion"],
            ],
            "drop_from_previous": [
                totals["Stage 1: Grade 7"] - totals["Stage 2: Grade 11"],
                totals["Stage 2: Grade 11"] - totals["Stage 3: Graduation"],
                totals["Stage 3: Graduation"] - totals["Stage 4: University"],
                totals["Stage 4: University"] - totals["Stage 5: Completion"],
            ],
        }
    )


@st.cache_data(ttl=3600)
def load_anomaly_map_data(
    db_path: Path = DEFAULT_DB_PATH,
    geojson_path: Path = DEFAULT_GEOJSON_PATH,
) -> pd.DataFrame:
    df = _fetch_df(
        """
        with leak as (
            select
                ags,
                region,
                avg(leakage_differential) as mean_leakage_differential
            from gold_leakage_differential
            group by 1, 2
        )
        select
            t.ags,
            t.region,
            t.end_to_end_completion_rate,
            t.compounded_transition_rate,
            coalesce(l.mean_leakage_differential, 0.0) as mean_leakage_differential,
            (
                (1.0 - coalesce(t.end_to_end_completion_rate, 0.0))
                + abs(coalesce(l.mean_leakage_differential, 0.0))
            ) as anomaly_score
        from gold_transition_rates t
        left join leak l using (ags, region)
        """,
        db_path=db_path,
    )

    if df.empty:
        return df

    df = df.copy()
    df["ags"] = df["ags"].astype(str).str.zfill(5)

    centroid_df = load_geojson_centroids(geojson_path=geojson_path)
    if not centroid_df.empty:
        df = df.merge(centroid_df, on="ags", how="left")
    else:
        df["lat"] = pd.NA
        df["lon"] = pd.NA

    missing_coords = df["lat"].isna() | df["lon"].isna()
    fallback = df.loc[missing_coords, "ags"].apply(ags_to_lat_lon)
    if not fallback.empty:
        fallback_df = pd.DataFrame(fallback.tolist(), index=fallback.index, columns=["lat", "lon"])
        df.loc[fallback_df.index, "lat"] = fallback_df["lat"]
        df.loc[fallback_df.index, "lon"] = fallback_df["lon"]

    df["map_source"] = "geojson"
    df.loc[missing_coords, "map_source"] = "pseudo"

    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    return df


@st.cache_data(ttl=3600)
def load_subject_resilience(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    return _fetch_df(
        """
        select
            hs_fg2_group,
            demographic_group,
            avg(subject_completion_share) as avg_subject_completion_share,
            sum(passed_exams) as passed_exams,
            sum(total_passed_exams) as total_passed_exams
        from gold_subject_resilience
        group by 1, 2
        order by avg_subject_completion_share desc
        """,
        db_path=db_path,
    )


@st.cache_data(ttl=3600)
def load_scd_timeline(mode: str, db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    if mode == "current":
        query = (
            """
            select
                ags,
                region,
                latest_year,
                cast(null as timestamp) as dbt_valid_from,
                cast(null as timestamp) as dbt_valid_to,
                'current' as record_type
            from int_district_current
            order by ags
            """
        )
    else:
        query = (
            """
            select
                ags,
                region,
                latest_year,
                dbt_valid_from,
                dbt_valid_to,
                'historical' as record_type
            from snapshots.snap_district_boundaries
            order by ags, dbt_valid_from
            """
        )

    return _fetch_df(query, db_path=db_path)


@st.cache_data(ttl=3600)
def load_evidence_metadata(artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> dict[str, object]:
    report_path = artifact_dir / "phase07_report.json"
    quality_path = artifact_dir / "phase08_quality_report.json"

    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.exists() else {}

    return {
        "phase07_report_present": report_path.exists(),
        "phase08_report_present": quality_path.exists(),
        "phase07_cluster_count": report.get("cluster_count"),
        "phase07_forecast_method": report.get("forecast_meta", {}).get("method"),
        "phase08_status": quality.get("status"),
        "phase08_fail_count": quality.get("fail_count"),
        "phase08_warn_count": quality.get("warn_count"),
    }
