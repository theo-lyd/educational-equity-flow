"""Phase 07 clustering and forecasting pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - import availability differs across environments
    Prophet = None  # type: ignore[assignment]


ARTIFACT_DIR = Path("warehouse") / "artifacts"
DB_PATH = Path("warehouse") / "analytics.duckdb"
MIN_POINTS_FOR_PROPHET = 4


@dataclass
class ForecastMeta:
    method: str
    source_metric: str
    train_points: int
    fallback_reason: str | None


def _get_connection(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path))


def load_feature_frame(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    query = """
    with leakage as (
        select
            ags,
            avg(leakage_differential) as avg_leakage_differential,
            avg(international_share) as avg_international_share
        from gold_leakage_differential
        group by 1
    ),
    resilience as (
        select
            ags,
            avg(subject_completion_share) as avg_subject_completion_share
        from gold_subject_resilience
        where coalesce(demographic_group, 'INSGESAMT') = 'INSGESAMT'
        group by 1
    )
    select
        t.ags,
        t.region,
        t.transition_rate_1_to_2,
        t.transition_rate_2_to_3,
        t.transition_rate_3_to_4,
        t.transition_rate_4_to_5,
        t.end_to_end_completion_rate,
        t.compounded_transition_rate,
        coalesce(l.avg_leakage_differential, 0.0) as avg_leakage_differential,
        coalesce(l.avg_international_share, 0.0) as avg_international_share,
        coalesce(r.avg_subject_completion_share, 0.0) as avg_subject_completion_share
    from gold_transition_rates t
    left join leakage l using (ags)
    left join resilience r using (ags)
    where t.ags is not null
    """
    return con.execute(query).fetchdf()


def _choose_k(x: pd.DataFrame, k_min: int = 2, k_max: int = 6) -> int:
    x = x.copy()
    for col in x.columns:
        if x[col].isna().all():
            x[col] = 0.0

    preprocess = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    x_transformed = preprocess.fit_transform(x)

    n_rows = len(x)
    if n_rows < 3:
        return 1

    upper = min(k_max, n_rows - 1)
    best_k = max(k_min, 2)
    best_score = float("-inf")

    for k in range(max(k_min, 2), upper + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(x_transformed)
        score = silhouette_score(x_transformed, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def _cluster_labels(cluster_summary: pd.DataFrame) -> dict[int, str]:
    ranked = cluster_summary.sort_values(
        by=["mean_end_to_end_completion_rate", "mean_transition_rate_4_to_5"],
        ascending=[False, False],
    ).reset_index(drop=True)

    narratives = [
        "High Resilience",
        "Stable Transition",
        "Recovery Potential",
        "High Leakage Risk",
        "Data Sparse Segment",
        "Emerging Segment",
    ]

    mapping: dict[int, str] = {}
    for idx, row in ranked.iterrows():
        label = narratives[idx] if idx < len(narratives) else f"Segment {idx + 1}"
        mapping[int(row["cluster_id"])] = label
    return mapping


def run_clustering(
    features: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int | float]]:
    feature_cols = [
        "transition_rate_1_to_2",
        "transition_rate_2_to_3",
        "transition_rate_3_to_4",
        "transition_rate_4_to_5",
        "end_to_end_completion_rate",
        "compounded_transition_rate",
        "avg_leakage_differential",
        "avg_international_share",
        "avg_subject_completion_share",
    ]

    model_input = features[feature_cols].copy()
    for col in model_input.columns:
        if model_input[col].isna().all():
            model_input[col] = 0.0

    k = _choose_k(model_input)

    if k == 1:
        features = features.copy()
        features["cluster_id"] = 0
        summary = pd.DataFrame(
            [
                {
                    "cluster_id": 0,
                    "district_count": int(len(features)),
                    "mean_end_to_end_completion_rate": float(
                        features["end_to_end_completion_rate"].fillna(0).mean()
                    ),
                    "mean_transition_rate_4_to_5": float(
                        features["transition_rate_4_to_5"].fillna(0).mean()
                    ),
                    "mean_leakage_differential": float(
                        features["avg_leakage_differential"].fillna(0).mean()
                    ),
                    "cluster_label": "Data Sparse Segment",
                }
            ]
        )
        return features, summary, {"selected_k": 1, "silhouette": 0.0}

    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=k, random_state=42, n_init=20)),
        ]
    )
    cluster_ids = pipeline.fit_predict(model_input)

    features = features.copy()
    features["cluster_id"] = cluster_ids

    summary = (
        features.groupby("cluster_id", as_index=False)
        .agg(
            district_count=("ags", "count"),
            mean_end_to_end_completion_rate=("end_to_end_completion_rate", "mean"),
            mean_transition_rate_4_to_5=("transition_rate_4_to_5", "mean"),
            mean_leakage_differential=("avg_leakage_differential", "mean"),
        )
        .sort_values("cluster_id")
        .reset_index(drop=True)
    )

    label_map = _cluster_labels(summary)
    summary["cluster_label"] = summary["cluster_id"].map(label_map)
    features["cluster_label"] = features["cluster_id"].map(label_map)

    transformed = pipeline.named_steps["scaler"].transform(
        pipeline.named_steps["imputer"].transform(model_input)
    )
    silhouette = float(silhouette_score(transformed, cluster_ids))

    return features, summary, {"selected_k": int(k), "silhouette": silhouette}


def load_stage5_timeseries(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    query = """
    select
        stage_5_year as year,
        sum(stage_5_degree_completions) as value
    from gold_stage_funnel
    where stage_5_year is not null
      and stage_5_degree_completions is not null
    group by 1
    order by 1
    """
    ts = con.execute(query).fetchdf()
    if ts.empty:
        return pd.DataFrame(columns=["year", "value"])
    ts["year"] = ts["year"].astype(int)
    ts["value"] = ts["value"].astype(float)
    return ts


def build_naive_forecast(series: pd.DataFrame, periods: int = 5) -> pd.DataFrame:
    if series.empty:
        raise ValueError("Cannot build forecast from empty series")

    last_year = int(series["year"].max())
    last_value = float(series.loc[series["year"] == last_year, "value"].iloc[-1])

    rows = []
    for step in range(1, periods + 1):
        year = last_year + step
        rows.append(
            {
                "year": year,
                "yhat": last_value,
                "yhat_lower": last_value * 0.95,
                "yhat_upper": last_value * 1.05,
            }
        )
    return pd.DataFrame(rows)


def build_linear_forecast(series: pd.DataFrame, periods: int = 5) -> pd.DataFrame:
    if len(series) < 2:
        raise ValueError("Linear forecast requires at least two points")

    ordered = series.sort_values("year")
    x = ordered["year"].to_numpy(dtype=float)
    y = ordered["value"].to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)
    residual_std = float(np.std(y - (slope * x + intercept), ddof=1)) if len(y) > 2 else 0.0

    last_year = int(x.max())
    rows = []
    for step in range(1, periods + 1):
        year = last_year + step
        yhat = float(slope * year + intercept)
        band = max(residual_std, abs(yhat) * 0.03)
        rows.append(
            {
                "year": year,
                "yhat": yhat,
                "yhat_lower": yhat - band,
                "yhat_upper": yhat + band,
            }
        )

    return pd.DataFrame(rows)


def run_forecast(series: pd.DataFrame, periods: int = 5) -> tuple[pd.DataFrame, ForecastMeta]:
    if len(series) >= MIN_POINTS_FOR_PROPHET and Prophet is not None:
        try:
            train = series.rename(columns={"year": "ds", "value": "y"}).copy()
            train["ds"] = pd.to_datetime(train["ds"].astype(str) + "-12-31")

            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=False,
                daily_seasonality=False,
            )
            model.fit(train)

            future = model.make_future_dataframe(periods=periods, freq="Y")
            fc = model.predict(future).tail(periods)[
                ["ds", "yhat", "yhat_lower", "yhat_upper"]
            ].copy()
            fc["year"] = fc["ds"].dt.year
            out = fc[["year", "yhat", "yhat_lower", "yhat_upper"]]

            return out, ForecastMeta(
                method="prophet",
                source_metric="stage_5_degree_completions",
                train_points=int(len(series)),
                fallback_reason=None,
            )
        except Exception:
            if len(series) >= 2:
                out = build_linear_forecast(series, periods=periods)
                return out, ForecastMeta(
                    method="linear_trend",
                    source_metric="stage_5_degree_completions",
                    train_points=int(len(series)),
                    fallback_reason="prophet_runtime_error",
                )

            out = build_naive_forecast(series, periods=periods)
            return out, ForecastMeta(
                method="naive_last_value",
                source_metric="stage_5_degree_completions",
                train_points=int(len(series)),
                fallback_reason="prophet_runtime_error",
            )

    if len(series) >= 2:
        out = build_linear_forecast(series, periods=periods)
        return out, ForecastMeta(
            method="linear_trend",
            source_metric="stage_5_degree_completions",
            train_points=int(len(series)),
            fallback_reason="insufficient_time_points_for_prophet",
        )

    out = build_naive_forecast(series, periods=periods)
    return out, ForecastMeta(
        method="naive_last_value",
        source_metric="stage_5_degree_completions",
        train_points=int(len(series)),
        fallback_reason="insufficient_time_points_for_prophet",
    )


def run_all(db_path: Path = DB_PATH, artifact_dir: Path = ARTIFACT_DIR) -> dict[str, object]:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    con = _get_connection(db_path)
    features = load_feature_frame(con)
    cluster_assignments, cluster_summary, cluster_metrics = run_clustering(features)

    stage5_series = load_stage5_timeseries(con)
    forecast, forecast_meta = run_forecast(stage5_series, periods=5)

    cluster_assignments_path = artifact_dir / "phase07_cluster_assignments.csv"
    cluster_summary_path = artifact_dir / "phase07_cluster_summary.csv"
    forecast_path = artifact_dir / "phase07_forecast.csv"

    cluster_assignments.sort_values(["cluster_id", "ags"]).to_csv(
        cluster_assignments_path, index=False
    )
    cluster_summary.sort_values("cluster_id").to_csv(cluster_summary_path, index=False)
    forecast.sort_values("year").to_csv(forecast_path, index=False)

    report = {
        "run_type": "phase_07_ml_forecasting",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "db_path": str(db_path),
        "cluster_assignment_rows": int(len(cluster_assignments)),
        "cluster_count": int(cluster_summary["cluster_id"].nunique()),
        "cluster_metrics": cluster_metrics,
        "forecast_meta": asdict(forecast_meta),
        "forecast_rows": int(len(forecast)),
        "artifacts": {
            "cluster_assignments": str(cluster_assignments_path),
            "cluster_summary": str(cluster_summary_path),
            "forecast": str(forecast_path),
        },
    }

    report_path = artifact_dir / "phase07_report.json"
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    con.close()
    return report


def main() -> int:
    report = run_all()
    print(
        "Phase 07 complete:",
        f"clusters={report['cluster_count']}",
        f"cluster_rows={report['cluster_assignment_rows']}",
        f"forecast_rows={report['forecast_rows']}",
        f"forecast_method={report['forecast_meta']['method']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
